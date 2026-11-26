VERDICT: APPROVED

## REVIEW_V4b.md - V4b, round 1 (word for word)

VERDICT: CHANGES REQUIRED
# REVIEW_V4b - round 8 (job R-V4b of SUNDAY_PLAN_29NOV.md): the inserted edits, the addendum 3.0c, Step 1's addresses
WHO: the design reviewer of row R-V4b, Fable 5.2; I wrote nothing of the memo, of rounds 3 to 7 or of the addendum. Thu 26 Nov 2026, 18:45 UTC
(clock read). THE MEMO CHECKED: `DESIGN_V4b.md`, 227,269 bytes, 1,570 lines, sha256 38ad7995...68eb, LF only, no control character (counted).
READ: `INSERT_V4b_REPORT.md`, `REVIEW_ROUND7_V4b.md`, `PACK_V4b_ROUNDS.md`, `PACK_CHECKLISTS.md` whole; of the memo ONLY: its head (1-14),
Step 1 and Step 2 (136-271), the top of Step 3 (273-295), the addendum (489-651), lines 1368, 1521, 1543, and the passages of lines 994, 1103
and 1105 the report names. `DEFERRED_TRIAGE.md` lines 207, 211, 213. CODE at 8edef01 (the tree is clean), by lines: `strategy.py` 344-347,
404-430, 470-542, 568-575, 702-709, 719-751; `scoreboard.py` 29-34, 62-71; `risk.py` 64-72; `memos.py` 78-84; `registry.py` 10, 46-47, 145-146;
`schemas.py` 91-97; `publish.py`'s `part=` lines; `proving/breaks/V4.json` 520-526. The `locator` found the memo functions.
RUN: two read-only scripts of my own (the replay below; the anchor counts), 13 address requests, two reads of source 6. No test, no
pipeline run. HOLD_TESTS was absent at each run. Nothing of the repo, of `proving/` or STATE.json was touched; nothing committed.

## THE VERDICT IN SIX LINES
1. THE INSERTED EDITS ARE IN, WORD FOR WORD AND COMPLETE - proven by my own replay, not taken from the report (section A).
2. T1 AND K1's FIRST REPLACE stand in the designer of record's wording; both hold the reviews' rule and their tests and breaks (section B).
3. STEP 1 holds 13 https addresses (5 are needed); all 13 answer; source 6's two November entries stand on the page as the memo gives them.
   Step 2 holds six lettered designs and the word ORIGINAL. "DEPENDS ON: none" and "BREAKS SHARE: 120" stand as the card's form asks.
4. THE ADDENDUM gives each of the three miss ids its step (207 -> 0d, 211 -> 0e, 213 -> 0f). THREE THINGS IN IT MUST CHANGE: one break is a
   double of a break V4 already holds and the sentence that says otherwise is untrue (C1); 0d's new problem memo has no code that closes
   it (C2); 0d's new answer to his tap promises a time the code does not keep (C3).
5. TO VERIFY POINT 11 (paid placement): V4b's memo need NOT act beyond what point 11 says. The fault is real and is the UPLOAD's - read by
   me, section D - and goes to the coordinator as a job of its own before the first live upload.
6. Ten small edits in all, every anchor counted exactly once. Nothing outside 3.0c and the two counting lines is touched.

## A. THE INSERTED EDITS - MY OWN REPLAY
METHOD: a script of mine read ANCHOR and TEXT from `PACK_V4b_ROUNDS.md` (rounds 3 to 6) and `REVIEW_ROUND7_V4b.md` (round 7), took
`PREDESIGN_V4b.md` (191,477 bytes, sha256 52924d18...02f1 - the report's start), applied rounds 5, 6, 7 in order (whitespace runs match any
whitespace run; every anchor found exactly once) and compared the result with `DESIGN_V4b.md` line by line.
- after round 5: 193,106 bytes, sha256 d6a208d8...31ec; after round 6: 193,955 bytes, 2a6c8e88...878c (the memo round 7 checked); after
  round 7: 194,842 bytes, cf2f7d50...c7e5. All three EQUAL the report's chain.
- THE FINAL FILE DIFFERS FROM MY ROUND-7 TEXT IN 15 PLACES AND NO OTHER (8 lines changed or replaced, 250 added): the head (1-14); line
  81's "####"; the https addresses in sources 1 to 5 (138, 141, 146, 149, 151); the new source block (153-194); the thirteen rows (234-249);
  lines 274-276; the size table's rows 0d, 0e, 0f (292-294); the addendum (489-651); line 1368; the DOCS line (1418); TO VERIFY 11 (1543).
  So lines 994 and 1105 are exactly the round-7 text: N1, N2, N3, N4, M1a, M1b, M1c, M2, L1 + L2, L-TESTS are in, each once, nothing else moved.
- ROUNDS 3 AND 4, counted in the final file: every TEXT stands exactly once and every replaced ANCHOR zero times (T2 two, T3 three, T4 six
  with the emptied one, T5, K1's second, K2) - EXCEPT the two the designer named: T1 and K1's first REPLACE (section B).

## B. THE TWO EDITS IN THE DESIGNER OF RECORD's WORDING - BOTH STAND
- T1 (the backstop never takes a public flagship down): line 994 says ""SCHEDULED" with its public time (`public_at`, else `slot_et`)
  still ahead of `now` (R24's T1: from its slot on the video is out, and this step never takes a public video down - only his own tap
  does)". The same rule, the same two clocks. Its test and its break ("the slot test removed from (0)") stand in line 1103.
- K1, first REPLACE (his KILL of an uploaded flagship ends the pair): line 994 holds K1's rule word for word up to "the killed film's
  question", then goes further (the Part 2 is ended, the row is sent once ever). Rounds 5, 6 and 7 read exactly this text and anchored on
  it; the review's own text can no longer be inserted and would undo them. K1's test and break stand in line 1105 ("ROUND 4 TESTS").

## C. THE REQUIRED CHANGES (each anchor counted by script: EXACTLY ONCE in the memo at 227,269 bytes; whitespace runs match any whitespace run; REPLACE = the anchor becomes the text; AFTER = right after the anchor)
**C1. THE BREAK ADDED FOR P8 IS A DOUBLE, AND THE SENTENCE THAT DENIES IT IS UNTRUE (0f; lines 626-631, 294, 276).** `proving/breaks/V4.json`
lines 520-526 hold break F-06: file `whatifs/scoreboard.py`, find `c = have[-1]; day = dt.date.fromisoformat(str(c["date"]))`, replace
`c = have[-1]; day = _day(now)`, caught by `test_the_pace_is_the_newest_readings_when_the_brief_leaves_before_the_days_reading` - the very
break 0f "adds". A double proves nothing new, and the memo's own rule would then make the typist invent another (A4: he decides nothing).
REPLACE
ANCHOR: P8 - CONFIRMED AS BUILT, AND NOW HELD BY A BREAK.
TEXT: P8 - CONFIRMED AS BUILT, AND HELD BY V4's OWN BREAK F-06.
REPLACE
ANCHOR: No test is added. BREAK ADDED to V4b's list (`whatifs/scoreboard.py`): find `    c = have[-1]; day = dt.date.fromisoformat(str(c["date"]))` -> `    c = have[-1]; day = _day(now)` - caught by that test (V4's list holds no break at this place: `have[-1]` is not in `proving/breaks/V4.json`).
TEXT: No test and no break is added (R-V4b, round 8): V4's own list already holds this very break - `proving/breaks/V4.json`, id F-06, the same find and the same replace, caught by that test - and a second one in V4b's list would be a double.
REPLACE
ANCHOR: no code; one test with step 10, two breaks |
TEXT: no code; one test and one break, both with step 10 |
REPLACE (the count; with C2's break the sum stays 120)
ANCHOR: 0d 3, 0e 9, 0f 2,
TEXT: 0d 4, 0e 9, 0f 1,

**C2. 0d's NEW PROBLEM MEMO IS NEVER CLOSED (0d; lines 525-527, 549-559).** `_undo_memo` writes a problem memo to D12 with `done_when`
"<key> reads <old>". V4's own stuck memo is closed by code when its proof comes (`settle` 522-525). This one has no closer: when he
sets the cell himself - the very act the brief's line offers him - `settle` 536 marks the row `undo_done` and the memo stays LIVE; the
watchdog escalates a live problem memo that is late (`memos.py` 343-346) for ever, and the week's line counts a problem that is over.
(It does not reach him: the memo is not `owner_visible`. `registry.EVERYONE` holds `problem_memo`, so D12 takes it: checked.)
AFTER
ANCHOR: "done_when": f"{r['key']} reads {r['old']}"}`.
TEXT (the eleven lines between the two rows of dashes, as they stand, starting on a new line):
----------
  (c2) THE STUCK MEMO IS CLOSED BY CODE WHEN ITS `done_when` COMES TRUE (R-V4b, round 8: `_back`'s stuck memo has its closer, 522-525; without one this memo stays live and the watchdog escalates it for ever - also after he set the cell himself). In `settle`'s stack loop the line `if _cell(key) == str(r["old"]): _save(st, r, numbers=dict(nums, undo_done=iso(now))); continue` becomes:
  ```python
            if _cell(key) == str(r["old"]):
                _save(st, r, numbers=dict(nums, undo_done=iso(now)))
                if nums.get("undo_stuck"):                                          # V4b step 0d: the stuck memo closes with its proof
                    for sm in MEM.find(st, type="problem_memo", from_dept="D1"):
                        if sm.get("dedupe_key") == f"strategy_stuck|undo|{r['id']}":
                            try: MEM.resolve(sm["id"], "D1", "repair_verified", f"Decisions:{r['id']}", "the cell reads the value of his Undo", st, now)
                            except Exception as e: log(f"strategy: the undo's stuck memo was not closed: {scrub(e)[:120]}", "WARN")
                continue
  ```
----------
AFTER (test (2))
ANCHOR: still two tickets, neither sentence in `b`, still one memo.
TEXT:  THEN (R-V4b, round 8), the three plants still standing: the cell is set to the decision's `old` with `core.set_setting`, `STR.settle(day 6)` -> the row's `numbers` hold `undo_done` and `MEMO.find(type="problem_memo", from_dept="D1")` holds no memo with that `dedupe_key` (it is resolved, kind "repair_verified"); a resolve that raises here is a FINDING, sent to the coordinator with TG11 (ii)'s (both use `_back`'s form, which no test has run until now).
AFTER (its breaks)
ANCHOR: -> `**{}` - caught by test (2) on day 1.
TEXT:  (4) find `if sm.get("dedupe_key") == f"strategy_stuck|undo|{r['id']}":` -> `if False:` - caught by test (2) at its last act (the memo is still live).
WHY `sm` AND THE OTHER LOG WORDS: `breaks.py` 56 makes a break VOID when its find stands twice in the file; `for m in MEM.find(...)` and
"the stuck memo was not closed" stand at 522 and 525 already. No break list in `proving/breaks/` holds either today (searched); this keeps
it so. THE CODE ABOVE WAS WRITTEN FROM READING 522-525 AND `memos.resolve`'s signature (208), NOT RUN - as 0d's own lines.

**C3. THE NEW ANSWER TO HIS TAP PROMISES A TIME THE CODE DOES NOT KEEP (0d (a); lines 505, 546, 557).** "goes back to <old> by the next daily
review": at the next daily review `settle` only WRITES the ticket (or finds the first one still waiting); the cell moves when the engine
takes that ticket - at its next tick, and between videos when a production runs (`undo`'s own words at 738 and 745). The step's title is
"an Undo says only what happened". "after" is true on every road of the `except` (a ticket written and taken earlier only comes sooner).
REPLACE
ANCHOR: goes back to {first['old']} by the next daily review (the change did not finish now)"`;
TEXT: goes back to {first['old']} after the next daily review (the change did not finish now)"`;
REPLACE
ANCHOR: holds "by the next daily review" and no
TEXT: holds "after the next daily review" and no
REPLACE
ANCHOR: (1) find `by the next daily review (the change did not finish now)"` -> replace
TEXT: (1) find `after the next daily review (the change did not finish now)"` -> replace

## D. TO VERIFY POINT 11 - PAID PLACEMENT: WHAT I READ, AND WHOSE IT IS
- THE PAGE (source 6, read by me today): 16 Nov 2026 - the property "no longer defaults to `false`"; a `videos.insert` or `videos.update`
  that leaves it out means "the video isn't declared as free of paid product placement"; to declare it, "explicitly set the property to
  `false`". The page does not say what an update of `status` or `snippet` alone does. The memo's source 6 gives this truly.
- THE CODE (8edef01): the upload asks `videos?uploadType=resumable&part=snippet,status` (`publish.py` 104, 108) and the text
  `paidProductPlacement` stands NOWHERE in `whatifs/`. So since 16 Nov 2026 every upload this engine makes - Short, long, pair video - is
  "not declared". Every change of privacy is a PUT of `videos?part=status` with the status alone (170, 284, 294).
- THE JUDGEMENT: V4b's acts name only the parts `status` and `snippet`; the declaration is a part of its own, which an update leaves alone
  unless it is named (the API's rule for parts - my reasoning, not the page's sentence; point 11 (a) keeps it as a thing the typist of step 5
  writes into the record: right). NO STEP OF V4b IS OWED. What is owed is the base's: `publish.yt_body` says `false`, the upload names the
  part, `yt_read` shows it back, a row of `release.SHEET` and of `PLATFORM_FACTS.md`, a test - a protected file, every kind of upload. It
  is a job of its own for the coordinator, to be in before the first live upload (the launch), not inside V4b.

## E. SAID, NOT REQUIRED
- 0d's LINE NUMBERS are one or two off in five places; every quoted TEXT is right and stands once, and the step says "found again by its
  TEXT". As read at 8edef01: the save before the `try` is 730 (memo: 729, twice); the `MEM.write` save is 741 (memo: 743); `brief`'s
  `elif r["state"] == "undone": continue` is 417 (memo: 419, twice); the stack loop is 532-541 (memo: 533-541) and its part from
  `_ticket_in_flight` is 537-541 (memo: 538-541).
- THE STUCK LINE IN A STACK: the row that rests is the NEWEST of the stack, so "set <key> to <its old>" names the next step back, not the
  value of the decision he tapped. It still works: once the cell reads that value, 536 marks the row done and the loop sends the older
  row's ticket by itself. The line offers a hand step on the Settings tab; it is his option, never a need (the default is said: "stays"),
  and no one-tap road exists that would not write a cell around the engine's own refusal.
- THE THIRTEEN PASTED ROWS (234-246): compared by script with `DESIGN_V4B_RECORD.md` 83-95 - 13 of 13 equal, word for word. They may stay:
  the sentence above the table already says they "are pasted with this memo", and the line under them says Step 3 decides. One number:
  TO VERIFY point 6 (line 1521) says "lines 81-95"; 81-82 are that table's header, the rows are 83-95 as line 247 says.
- SOURCE 6 names the entries of 16 Nov and 2 Nov 2026. The page also holds one of 3 Nov 2026 (read by me): `thumbnails.set` now takes a
  custom thumbnail for a Short once processing is complete, and the resource gains `shortsAspectRatio`. Not V4b's (D9's release; parked).
- THE NINE TEST GAPS: I do not know the lost report either. Each of 0e's nine `find` texts stands exactly once in its file at 8edef01
  (counted); TG7, TG11, TG13, TG14, TG15, TG16 and TG17 I read against the code and each test as written fails under its break. TG8's six
  readers and TG12 I did not open; 0e's own rule (a test red on the code as it stands is a FINDING) covers a wrong reading.
- `INSERT_V4b_REPORT.md` line 92 still says "one break added on its existing test" for P8; it follows C1 if the report is touched.

## F. 5.4's TEN QUESTIONS, FOR WHAT IS NEW IN THIS ROUND (the rest of Step 3 was answered in rounds 3 to 7)
 1. A layman's gain: YES - 0d: he is told the truth about his Undo, once; 0e and 0f are an audit's closure (tests), no new machine.
 2. His words: YES - item 150 (no ask without a default: both new lines say what happens if he does nothing), item 169 (nothing asked
    of him); V4's approved promise of the "sent again" line is kept. Nothing forgotten that I found.
 3. Enforceable: YES after C1 to C3 - every rule of 3.0c has a test that fails and a break with exact text; before them one break was a
    double and one memo had no closer.
 4. Taste by a cheap model: NO - the addendum makes no model call.
 5. Finished file: NOT TOUCHED - no measure of a video is added.
 6. Money: YES - no paid call, no cost line (said in each step).
 7. Reuse: YES - `_back`'s memo form, V4's `briefed` stamp, the fixtures of V4's test file; `tools/sweep.py` is left as it is.
 8. Older pins: YES - searched again by me: no test or tool pins `undo`'s `except` sentence ("between videos" stands in `test_v12_exec.py`
    99 and 163 for the engine's own words only); no break list holds `undo_sent`, `undo_done` or `_ticket_in_flight`.
 9. The worst video: NONE NEW - 3.0c touches no path a video takes.
10. Only reality: how the engine's refusal note reads to him inside a real brief (it is the engine's own text, cut at 200 characters).

## FOR THE COORDINATOR
The first line turns to APPROVED when the ten edits of C1 to C3 are in the memo by script (each anchor once) and one reader has seen the
(c2) hunk beside `strategy.py` 522-525 and 536. Section D's fault is NOT V4b's and waits for nobody in this batch: it needs a job of its own.

## NOT READ
The memo outside the lines named above (Step 3's steps 0a to 0c and 1 to 11, 3.13, 3.14 but line 1368, the last three sections but two
lines): reviewed in rounds 3 to 7, not again. `dash.py` and `finance.py` beyond the counted lines; `notify.digest`; `caretaker`, `governor`,
`manage.monthly_brief` (TG8); `scoreboard.line`; `memos.resolve`'s body; `execute.overview`. Sources 1 to 5 and 7 to 10: asked for and
answered (HTTP 200), their sentences not read again by me. No test was run: every "fails under its break" above is from reading.

## REVIEW_V4b_2.md - V4b, round 2 (word for word)

VERDICT: APPROVED
# REVIEW_V4b_2 - round 2 of the U1 design review of V4b (row R-FOLD-U1 of SUNDAY_PLAN_29NOV.md, 6c line 3): are C1 to C3 of REVIEW_V4b.md in the memo
WHO: the design reviewer of row R-FOLD-U1, Fable 5.2 High; I wrote nothing of the memo, of REVIEW_V4b.md or of the fold. Thu 26 Nov 2026, 19:19 UTC
(`date -u`, read in this pass). THE MEMO CHECKED: `DESIGN_V4b.md`, 228,971 bytes, sha256 2a475b3b...c3c9 - equal to FOLD_U1_REPORT.md's AFTER line.
READ: FOLD_U1_REPORT.md whole; REVIEW_V4b.md whole (16.8 KB); of the memo ONLY what my script printed around each edit and lines 292-293, 505-546.
CODE at 8edef01: `whatifs/org/strategy.py` 516-543, `whatifs/org/memos.py` 137 and 208 (the two signatures).
RUN: one read-only script of my own (no test, no pipeline run; NOTES\HOLD_TESTS absent before each run). Nothing of the repo, of `proving/` or of
STATE.json was touched; nothing committed.

## A. THE TEN EDITS - MY OWN REPLAY, NOT THE REPORT'S
METHOD: the script cut every ANCHOR and TEXT from REVIEW_V4b.md by its line (52/53, 55/56, 58/59, 61/62, 70 + 73-83, 86/87, 89/90, 100/101,
103/104, 106/107), never retyped, and counted each in the memo (whitespace runs match any whitespace run, as the review orders).
| change | the TEXT stands | the replaced ANCHOR | at line | the place |
|---|---|---|---|---|
| C1-a | once | gone | 637 | P8's first sentence - sound |
| C1-b | once | gone | 640 | P8's last sentence, before P9 - sound |
| C1-c | once | gone | 294 | row 0f of the size table - sound |
| C1-d | once | gone | 276 | the BREAKS SHARE count line; `BREAKS SHARE: 120` stands once (275) - sound |
| C2-a | once, ALSO as exact text (the eleven lines byte for byte) | - (AFTER) | 528-538 | right after the anchor's line 527, before `(d)` - sound |
| C2-b | once, right after its anchor | - (AFTER) | 565 | test (2), before "Then, on a fresh Sheet" - sound |
| C2-c | once, right after its anchor | - (AFTER) | 570 | the break list of 0d, as its (4) - sound |
| C3-a | once | gone | 505 | `undo`'s `except` answer - sound |
| C3-b | once | gone | 557 | test (1) - sound |
| C3-c | once | gone | 568 | break (1) of 0d - sound |
COUNTED BESIDE: "by the next daily review" 0 times, "after the next daily review" 3 times (505, 557, 568); "HELD BY A BREAK" 0; "two breaks |" 0;
`0d 4, 0e 9, 0f 1` once. RESULT: all ten are in, word for word, each in a sound place. The sum 120 holds (0f gives one break, 0d takes one).

## B. THE (c2) HUNK BESIDE THE CODE (REVIEW_V4b's own condition: "one reader has seen the (c2) hunk beside `strategy.py` 522-525 and 536")
SEEN BY ME at 8edef01. Line 536 is exactly the line (c2) names: `if _cell(key) == str(r["old"]): _save(st, r, numbers=dict(nums, undo_done=iso(now))); continue`.
The hunk keeps its two acts (the save, the `continue`) and adds the closer in the form of 522-525: `MEM.find(st, type="problem_memo", from_dept="D1")`
is the call of 522; `MEM.resolve(sm["id"], "D1", "repair_verified", f"Decisions:{r['id']}", "<note>", st, now)` fits `resolve(mid, by, kind, ref,
note, st, now)` (memos.py 208); the `dedupe_key` is the one `_undo_memo` writes (memo line 524). The loop variable `sm` and the log words "the
undo's stuck memo was not closed" differ from 522 and 525, so break (4)'s find stands once in the file. The indentation is the stack loop's (12
spaces). (c) replaces 537-541 and (c2) replaces 536: the two do not overlap. `nums.get("undo_done")` at 535 keeps a closed row from being asked
again. NOT RUN, as the review says of its own lines.

## C. ONE WORD LEFT BEHIND BY THE FOLD - NOT REQUIRED, EXACT TEXT GIVEN (the typist types by the letters, not by the count)
Line 505 still says "four places"; with (c2) the lettered places are five: (a), (b), (c), (c2), (d). If the memo is touched again (anchor counted: once):
- FIND: ``four places of `strategy.py` and one cell``
- REPLACE BY: ``five places of `strategy.py` and one cell``
No step, test or break hangs on that word; typing does not wait for it.

## FOR THE COORDINATOR (none is a question to the owner)
- V4b's design is approved as it stands on disk (sha256 above). REVIEW_V4b.md section D (paid placement: the upload's fault, a job of its own before
  the first live upload) is unchanged by this round and still owed outside V4b.
- REVIEW_V4b.md section E's five line numbers of 0d (one or two off) were not edits and are still as they were; every quoted TEXT stands once.

## NOT READ
The memo outside the lines named above. `INSERT_V4b_REPORT.md`, the rounds 3 to 7. No test was run.

## REVIEW_DRAWN-b.md - DRAWN-b, round 1 (word for word)

VERDICT: CHANGES REQUIRED
SIX CHANGES, EACH A PLACE AND ITS EXACT WORDS (find -> replace, or a block to insert). NONE NEEDS A DESIGNER'S JUDGMENT: a clerk puts them into
`NOTES\DESIGN_DRAWN-b.md` word for word, or the typist of the step types from this file beside the memo - where this file and the memo differ, THIS FILE
WINS. WITH ALL SIX IN, THIS REVIEW APPROVES THE DESIGN WITHOUT ANOTHER ROUND (the reviewer reads the inserted lines, nothing else). Every "find" below was
counted in the memo by `grep -cF` at 18:45 UTC on 26 Nov 2026: each stands exactly once, but change 1's (twice, both replaced).
ONE THING IS NOT APPROVED BY ANYONE AND IS NOT IN THE MEMO: corrections C11 and C12 of 20 Nov (their text is lost; change 5 says what stands instead and
names the open item for the coordinator). Nothing here is work for the owner.

# REVIEW_DRAWN-b - the design review of `NOTES\DESIGN_DRAWN-b.md` (269,795 bytes, 1177 lines, as written 26 Nov 2026 18:34 UTC), row R-DRAWN-b, lane L2
By the DESIGN REVIEWER of row R-DRAWN-b (Fable 5.2, High). I wrote none of the memo and none of its check list. Clock: `date -u` read 18:44:34, 18:45:51 and,
after the file was written, 18:48:36 UTC on 26 Nov 2026. `NOTES\HOLD_TESTS` did not exist before my one run (checked in the same command).
WHAT I READ (the narrow read my row orders): the memo's lines 1-361 whole (head, Step 1, Step 2, the top of Step 3 with the twelve steps, miss 279,
FC-2, FC-3, the seed items, the nine rows, the places); of the rest only the lines the new parts stand on (3.4; test 3; test 20; 3.8's tests 7-14 and
breaks B-1 to B-23; F-10 to F-13; PART C's lines on the code's own scene, `DENY`, `_states`; C4's and C7's planted words; PART A's enforce table);
`CHECK_DRAWN-b.md` whole; `PACK_CHECKLISTS.md` whole; the review of record's verdict block and its headings; `drawnb_corrections_C1-C7.md` lines 26-55,
71-163; `DEFERRED_TRIAGE.md` lines 229, 230, 279; `02` 1122-1131. IN THE TREE (8edef01, clean before and after): `tools/rehearsal.py` 126-158,
`tools/sweep.py` 98-160, 222-246, 296-362 and its parser, `whatifs/scenes.py` 23-50, 215-357, `whatifs/fakes.py` 388-403, `whatifs/drawn.py` 151-169,
`whatifs/media.py` 280-296, `tests/conftest.py` 1-80, `tests/test_v111_enforce.py` 98-110, the matrix's rows 160-166.
THE ONE RUN (2.3 s; a scratch test file outside the repo, the repo's own fixtures; no production): the memo's code of steps 3 and 4 copied into the
scratch file and walked through the REAL `scenes.place`, the REAL `contract.p_drawn_plan` and `sweep.drawn_of` - 12 cases, results under change 1 and
in the attack list. The tree holds neither A0a nor A0b yet: the walk is on today's rules; what A0a and A0b add was checked by reading (below).

## THE GATE WORDS (my card)
- Step 1 holds 19 https addresses (5 needed): S1 to S14 each with one, seven of them DATED (S1 to S7). YES.
- Step 2 holds two lettered lists (PART A's A to E, PART B's A to D: 9 designs, 3 needed) and the word ORIGINAL on PART A's D and PART B's C. YES.
- Step 3 opens with `DEPENDS ON: none - ...` (line 193) and `BREAKS SHARE: 90 ...` (line 194). YES - and the number becomes 97 by change 5.
- The three headings stand once each, in order (lines 16, 158, 192). YES.

## THE SIX CHANGES

### 1 (STEP 4, A0d; REQUIRED - the `part` planting RAISES as typed, in the test and in the sweep)
`dict(mapping, **{i: part})` with `i` a number is `TypeError: keywords must be strings`. MEASURED: the memo's planting test, case "part", fails on
exactly that at the memo's line; with the line below it passes (the part is drawn, by "writer", and `p_drawn_plan` answers PASS). In the sweep the
call stands OUTSIDE `place`'s try (`replies = ask(ep, wanted) if wanted else {}`, `scenes.py` 337), so the walk's fourth run would have crashed the
production instead of drawing a part.
- FIND (twice: the code block of `plant_template`, line 242, and break AB-23's text, line 293): `dict(real_ask(ep_, wanted), **{i: part})`
- REPLACE BOTH BY: `{**real_ask(ep_, wanted), i: part}`
So the code line is `SCN.ask = lambda ep_, wanted: {**real_ask(ep_, wanted), i: part}` and AB-23 reads: in `plant_template`,
`SCN.ask = lambda ep_, wanted: {**real_ask(ep_, wanted), i: part}` made `SCN.ask = real_ask` (the planting test, part). MEASURED with the corrected
line: AB-23 is caught (the scene is the writer's `count`, the test's `template == "part"` fails); AB-22 is caught (a `count`, not a `compare`).

### 2 (STEP 4, break AB-21; REQUIRED - the test must fail for the reason the break names)
As worded, AB-21 (`and hit` removed) is caught only by a crash: `hit[0]` raises `IndexError` on the empty list (measured). The break is to make the
judge call a film good that drew ANOTHER template - then the test's own assert fails.
- FIND: ``AB-21 - in `drawn_template_of`, `and hit` removed from the `if` (the judge's test: "part" is judged good)``
- REPLACE BY: ``AB-21 - in `drawn_template_of`, `hit = [x for x in seen if x.startswith(template)]` made `hit = seen` (the judge's test: "part" is judged good on a film that drew "ladder1" - its assert `ok is False` fails)``

### 3 (STEP 5, L1a, break LB-9; REQUIRED - the designer's added pair is RIGHT and must stand where the test is typed from)
The designer's finding holds by arithmetic (`passes`: `yes * 100 >= bar * len(keys)`, line 638): bar 70 with 7 asked is 500 and 400 against 490 -
the same under `>=` and `>`; (a) and (b) of test 3 are 600 and 500 against 560 - the same too. Nothing of test 3 sits on the bar, so LB-9 is caught
by nothing. The pair bar 50 with 8 asked is 400 against 400: 4 passes under `>=` and fails under `>`. But the pair stands only in step 5's line, and
line 196 says the memo wins over that line - a typist of test 3 reads line 780 and never types it. Two edits:
- FIND (line 780): `(i) bar 70 with 7 asked: 5 passes, 4 fails;`
- REPLACE BY: `(i) bar 70 with 7 asked: 5 passes, 4 fails, and [MF, REVIEW_DRAWN-b change 3: ON THE BAR EXACTLY] bar 50 with 8 asked: 4 passes, 3 fails (400 against 400 - break LB-9's catch);`
- FIND (line 196): `and where a line here and the memo differ THE MEMO WINS.`
- REPLACE BY: `and where a line here and the memo differ THE MEMO WINS - but for what a line here marks as added or corrected (a bracket "[MF", "ONE FAULT FOUND WHILE MAKING FINAL", FC-2, FC-3, and the block "MF - THE CORRECTIONS OF 20 Nov TO B1 AND B2"), which stands.`

### 4 (PART B's NINE MATRIX ROWS; REQUIRED - two rows name the wrong tests, and as written no row is checked by the test the memo leans on)
(a) THE ROWS AGAINST THE OPUS MEMO's OWN LIST (3.8: B-1 to B-23 with their tests, lines 1081-1088; F-10 to F-13: B-24 to B-28, line 832), break by
break: all 28 breaks stand in exactly one row and in the right row (B1's nine in rows 1 to 5, B2's nineteen in rows 6 to 9). Two cells are wrong:
row 8 lists "tests 9, 10, 12" but its B-14 is caught by test 7 (`args(...)` has no "duration") and no break of row 8 is caught by test 12; row 7's
B-18 is caught by tests 9 AND 12. Rows 1 to 6 and 9: every break's test is in its row's cell.
(b) THE FORM: `tests/test_v111_enforce.py::test_every_owner_requirement_in_the_matrix_is_wired_to_a_real_check` (98-110, read) checks ONLY references
written `fn:<module>.<function>` or `contract:<check>`; a bare `living.frame_of` in backticks is read by nothing, so the memo's sentence "fails on a
row that names code which does not exist" is true only in that form. The typist is given the references, not left to derive them.
- FIND (line 338): ``The typist writes each in the form of the rows beside it in `docs/CURRENT/ENFORCEMENT_MATRIX.md`; `tests/test_v111_enforce.py` 98-100 fails on a row that names code which does not exist:``
- REPLACE BY: ``The typist writes each as ONE row of `docs/CURRENT/ENFORCEMENT_MATRIX.md` in that file's own three cells (the rule in the house's capitals; the references; the tests and breaks) and types every reference in the file's own form, because `tests/test_v111_enforce.py` 98-110 checks ONLY references of the forms `fn:<module>.<function>` and `contract:<check>`. THE REFERENCES, ROW BY ROW - 1: `fn:whatifs.living.frame_of` `fn:whatifs.living.render`; 2: `contract:living_characters`; 3: `fn:whatifs.living.variants` `fn:whatifs.living.shape_word`; 4: `fn:whatifs.living.envelope` `fn:whatifs.living.speaking` `fn:whatifs.episode._render`; 5: `fn:whatifs.living._sheet_rows`; 6: `fn:whatifs.clips.restyle` `fn:whatifs.clips.issues` `fn:whatifs.living.restyle_arm`; 7: `fn:whatifs.media.restyle` `fn:whatifs.living.restyle` `fn:whatifs.episode._render`; 8: `fn:whatifs.costguard.lines` `fn:whatifs.living.restyle` `fn:whatifs.clips.args` `fn:whatifs.sheets.identity_score`; 9: `fn:whatifs.clips.restyle_preflight` `fn:whatifs.preflight.run`. The same form holds for PART A's rows (Step 5 ENFORCE: `look.run` is typed `fn:whatifs.org.look.run`, `contract._look` as `contract:short_look` and, from L3, `contract:look_bar`). The table below gives each row's rule, code and catch:``
- FIND (row 2): `| test 2; B-21 |` - REPLACE BY: `| test 2; B-21, B-29 |`
- FIND (row 4): `| tests 4, 6; B-4 to B-6, B-8 |` - REPLACE BY: `| tests 4, 6; B-4 to B-6, B-8, B-30 |`
- FIND (row 7): `| tests 8, 9; B-15, B-17 to B-19, B-24, B-25, B-27 |` - REPLACE BY: `| tests 8, 9, 12; B-15, B-17 to B-19, B-24, B-25, B-27 |`
- FIND (row 8, the whole row): ``| 8 | The restyle's money is a line only while the arm can fire, by the second, capped at `RESTYLE_EST_S` seconds a video, with no circle in the estimate | `costguard.lines`, `living.restyle`, `clips.args` | tests 9, 10, 12; B-14, B-20, B-26 |``
- REPLACE BY: ``| 8 | The restyle's money is a line only while the arm can fire, by the second, capped at `RESTYLE_EST_S` seconds a video (an unreadable count closes the cap; a failed buy is counted), with no circle in the estimate; the identity judge of each restyled piece is a line of its own (`restyle_identity`) and is booked to the film it judges | `costguard.lines`, `living.restyle`, `clips.args`, `sheets.identity_score` | tests 7, 9, 10, c9; B-14, B-20, B-26, B-31 to B-34 |``
(the ids B-29 to B-34 are change 5's). CHECKED IN THE TREE: `living.render`, `variants`, `speaking`, `_sheet_rows`, `episode._render`,
`costguard.lines`, `preflight.run`, `sheets.identity_score` and the check `living_characters` exist today; the other names are typed by steps 11 and 12
before their row is.

### 5 (THE RULING ON C4 TO C12: C4 TO C10 JOIN THE MEMO, WITH SEVEN BREAKS; C11 AND C12 CANNOT - THEIR WORDS ARE LOST)
WHY THEY MUST JOIN: B1 and B2 are typed AGAIN from this memo (the typed-ahead patches are gone); each of C4 to C10 was found by a finisher or by R1 on
the typed code, typed, and proven red then green with a break of its own. Typed away, three things come back that the plan's review questions forbid:
a paid call with no line (C8: the identity judge of every restyled piece - 5.4 question 6); an older test turned red by B1 that the memo does not name
(C10: `tests/test_v12_inside.py`, the stand-in narration without `wav_path` - 5.4 question 8); and two rules of F-11 that only a test of their own
holds (C6: an unreadable count must CLOSE the cap; C7: a failed buy is counted). FC-2 and FC-3 STAY as the designer wrote them (same reason).
THEY JOIN BY NAME, NOT BY RETYPING: the file `NOTES\DRAWN_b_typed_ahead_patches\drawnb_corrections_C1-C7.md` holds each correction with the exact
line its break finds. I read its lines 26-55 and 71-163 against the memo: no correction contradicts a rule of 3.1 to 3.5 or of F-1 to F-13; C6 makes
F-11's "0 when missing" exact (missing = 0; there but unreadable = closed).
- INSERT, as a block of its own directly after the line that begins `- FC-3 (its C3): the recipe` (line 312):
```
MF - THE CORRECTIONS OF 20 Nov TO B1 AND B2 (C4 to C10) ARE PART OF THIS MEMO (ruled by REVIEW_DRAWN-b, change 5). Each was typed and proven red then green on the typed-ahead copy: `NOTES\DRAWN_b_typed_ahead_patches\drawnb_corrections_C1-C7.md`, lines 26-38, 44-54, 71-91 and 111-127 - the typists of steps 11 and 12 read those lines WITH this memo, and where they differ from the Opus memo's text or from F-1 to F-13 THEY WIN. The typed-ahead code is gone: each line a break's "find" quotes is typed exactly as that file quotes it. Seven breaks join the list:
- B-29 (C4; step 11): test 1 asserts the memo's own boxes `(555, 0, 1365, 1080)` and `(0, 192, 1080, 1632)`; test 2 gains the planted stretch through `render` (`shape_err` 1.37, `p_living` FAIL, then PASS restored). BREAK: in `living.render`, `shape_err = round(abs(((box[2] - box[0]) / max(1, box[3] - box[1])) / (art.shape[1] / art.shape[0]) - 1), 4)` made `shape_err = 0.0`; test 2 fails.
- B-30 (C5; step 11): test 6 gains the render that hears a WAV (sound only from second 12.9 of a word 12.5 to 13.5). BREAK: in `living.render`, `mouth = speaking(words, t0, fps, nframes, env=env) if mm else set()` made `mouth = speaking(words, t0, fps, nframes) if mm else set()`; test 6 fails.
- B-31 (C6; step 12; F-11 made exact): `living.restyle` reads `rst_booked.txt` with `except FileNotFoundError: booked = 0`; a file that is there but empty or unreadable logs a WARN and returns False - the cap is CLOSED, never counted as 0; test 9 gains the empty file. BREAK: `nothing more is restyled for this film, the code-made one stays", "WARN", ep); return False` made `nothing more is restyled for this film, the code-made one stays", "WARN", ep); booked = 0`; test 9 fails.
- B-32 (C7; step 12): test 9 gains the FAILED buy that is booked too. BREAK: the two lines `with open(bk, "w") as f: f.write(str(booked + n))` and `MD.restyle(src, RESTYLE_PROMPT.format(look=ANIM.style_lock()), keep, ep, seconds)` swapped; test 9 fails.
- B-33 (C8; step 12; a paid call gets its line): `costguard.lines` gains the line `restyle_identity`, a statement of its own directly after the `restyle` line and under the same `if rr_ is not None:` - n = `int(RESTYLE_EST_S // max(1, the row's min_s))` (20 at the defaults), unit = the NEW cell `RESTYLE_ID_EST_INR` "40" (`core.DEFAULTS`, after `RESTYLE_EST_S`; its note says it is a bound, not measured on a bill), stage "ai_writing", item None, calls `{"vision": None}`. Test 10 gains the line's checks and its own filter becomes `not in ("restyle", "restyle_identity")`. BREAK: `    if rr_ is not None: L.append(_line("restyle_identity",` made `    if False: L.append(_line("restyle_identity",`; test 10 fails.
- B-34 (C9; step 12): `sheets.identity_score(ref, new, who, episode="SHEETS")` hands `episode` to `ask_vision`; `living.variants` and `living.restyle` pass `episode=ep`. The masters' own call in `sheets.py` stays three arguments, so the three-argument stand-in of `tests/test_v12_owner.py` (1612 today) does not move. NEW TEST in `tests/test_v12_drawn_b.py`: `test_c9_the_identity_judgement_is_booked_to_the_film_it_judges`; the stand-ins of tests 3 and 9 take `episode=None`. BREAK: the line `sc = SH.identity_score(base_path, mid, char, episode=ep) if (base_path and ok) else None` of `whatifs/living.py` typed without `, episode=ep`; test c9 fails.
- B-35 (C10; step 11; an OLDER pin that B1 moves BY DESIGN - F-1 hands the cutaway `wav=vo.wav_path`): in `tests/test_v12_inside.py` the stand-in narration of `_render_record`, `vo=type("V", (), {"duration": t})()` (712 today), becomes `vo=type("V", (), {"duration": t, "wav_path": ""})()` with its comment ("" = no file: the mouth flaps by the older rule). BREAK: `{"duration": t, "wav_path": ""}` made `{"duration": t}`; `test_a_cutaway_whose_art_is_gone_continues_the_picture_in_its_acts_direction` fails.
OPEN FOR THE DAY HE OPENS THE RESTYLE (nothing at the launch: `RESTYLE_ON` FALSE, share 0, no line): `RESTYLE_ID_EST_INR` 40 x 20 is Rs 800 a long video beside a restyle of Rs 19.8 - a bound, and far above what the restyle it guards costs. One identity call is measured on a bill and the cell is set to the measured price BEFORE `RESTYLE_ON` is ever TRUE; the launch pack's line for the restyle says so.
NOT IN THIS MEMO, SAID PLAINLY - C11 AND C12 (R1-205, R1-208: the talking cast's bought variants and their identity calls as the lines `living_variants` and `living_identity` of the estimate, `living.variant_room`, five breaks). Their full text stood in the patch and in the finisher's later runs, which are lost; on disk only the headlines stand (that file's lines 131-163). NOTHING IS TYPED FROM A HEADLINE. The gap is OLDER than this batch (the accepted code buys those pictures inside `LIVING_VARIANTS_CAP_INR` with no line) and nothing fires at the launch (`LIVING_HIS_LOCK_ONLY` TRUE, no art locked by him). It is OWED INSIDE THIS BUILD as OPEN "DRAWN-b-C12": the row the coordinator names writes it again from those lines, as a step after B1, with a review of its own.
```
- FIND (line 194): `BREAKS SHARE: 90 (AB-1 to AB-23: 23; LB-1 to LB-40 without the retired LB-7: 39; B-1 to B-28: 28)`
- REPLACE BY: `BREAKS SHARE: 97 (AB-1 to AB-23: 23; LB-1 to LB-40 without the retired LB-7: 39; B-1 to B-35: 35)`
- FIND (line 196): `gets all 90, the three new ids at the end of the AB list.`
- REPLACE BY: `gets all 97, the three new AB ids at the end of the AB list and B-29 to B-35 at the end of the B list.`
- FIND (step 11): `ITS BREAK (one of nine: B-1 to B-8, B-21)` - REPLACE BY: `ITS BREAK (one of twelve: B-1 to B-8, B-21, B-29, B-30, B-35)`
- FIND (step 12): `ITS BREAK (one of 19: B-9 to B-20, B-22 to B-28)` - REPLACE BY: `ITS BREAK (one of 23: B-9 to B-20, B-22 to B-28, B-31 to B-34)`
- FIND (step 12): `` `whatifs/core.py` (five cells) `` - REPLACE BY: `` `whatifs/core.py` (six cells: the five and `RESTYLE_ID_EST_INR`) ``
- FIND (step 12): `plus one vision call a restyled piece (the identity gate); Rs 0 and no line at the launch.`
- REPLACE BY: ``plus the line `restyle_identity` - one identity judgement a restyled piece, n 20 at `RESTYLE_ID_EST_INR` Rs 40 (a bound, not a bill: Rs 800 a long video at most while all four locks are open); Rs 0 and no line at the launch.``
Older lines of the memo that still say 28, 85 or 90 breaks (F-5, the second table) are its history: lines 194 and 196 decide.

### 6 (STEP 4, ONE SENTENCE; REQUIRED WORDS - what the walk can and cannot say)
`drawn_template_of` reads `Video_Features`, which `brain.tag` writes only after the upload step (`episode.py` 874-879). A film that is HELD before
its upload has no such row: the judge then says "drawn: nothing" although the scene may have been drawn. That is a true "not proven", never a wrong
"good" - but the walk's reader must not take it for a refused scene.
- INSERT at the end of the paragraph that begins `THE WALK ITSELF - A MEASUREMENT OVER IDS` (line 294), after its last words `never a skipped test.`:
` A run whose words end "(drawn: nothing)" on a film that was HELD before its upload says only that the film's record was never written (the row of `Video_Features` is written after the upload): the reader names the hold from `problems`, and that run counts as NOT PROVEN, never as a refused scene.`

## THE NEW AND CHANGED PARTS, EACH RULED

### STEP 3 (A0c, miss 229) - SOUND AS WRITTEN; nothing to change
- THE FAULT IS REAL AND STANDS AS QUOTED: `tools/rehearsal.py` 149 (`ok12, said12 = inside12(...)`), 151 (the same two names take the drawn judge's
  answer), 152 (`print("drawn:", ...)`), 156 (`print("inside the format:", said12[:420])` prints the drawn words). The three find lines (a), (b), (c)
  each stand once in the file, word for word.
- THE NEW ASSERT CAN NEVER TURN A GOOD REHEARSAL RED: `sweep.inside_of` returns `True` only with words that begin "inside the format held:" (its last
  line, 157), and the rehearsal already asserts `ok12`.
- MEASURED on the file's text: the memo's test is RED today (first assert), GREEN with (a), (b), (c) typed (the changed file still compiles), RED
  again under AB-20. The regular expression does not take `saidd12 =` for `said12 =` and does not trip on `said12.startswith(`.
- F-9's PLACE HERE (doubt 6) is approved: it keeps the memo's own rule (TO VERIFY 10 first, nothing typed blind) and types nothing if the five runs
  do not draw. No matrix row and no switch: right - a tool's printed evidence, no product path.

### STEP 4 (A0d, miss 230) - SOUND WITH CHANGES 1, 2 AND 6
- THE CHOICE (a flag of the sweep, not a pytest production, not a changed offline Director) is right for the reason the memo gives: the older tests'
  cells are not the whole path, and a Director that varies by id moves every accepted film.
- MEASURED through the real plan step and the real gate check, on the test's own five lines: ladder, compare and flow are placed on unit 2, drawn by
  "writer", `p_drawn_plan` PASS - as typed. part: change 1. The judge's test passes as typed; AB-21: change 2.
- THE MEMO's THREE "A RUN DECIDES" PLACES (doubt 4), each now decided for TODAY's rules: the offline writer's flow of "The cup falls because the table
  tilts." passes `verify` (links "the table tilts", "The cup falls"); the layout takes all four planted scenes at the test's work size;
  `core.store().append` is how `test_t5_...` plants its rows (its line 624). The six ids EP203103070830 to ...0835 stand in no file of `tests/` or
  `tools/` (searched: the highest in use is ...0814).
- AGAINST A0a AND A0b, BY READING (they are not in the tree): the code's own scene never reaches a rule (line 439), so ladder and compare pass as
  before; the planted flow's own sentence and its next sentence in the test ("You look outside.") hold no word of `DENY` (line 445); the part's three
  sentences are C4's and C7's own words, and A0b reads SENTENCES across the three lines (`sentences(texts)`, line 561), so three sentences in one line
  are read as C7's three lines are. IN THE WALK the film's own next line follows the planted flow: if it holds a word of `DENY` the arrow is refused
  - the memo's own clause covers it (the words change, three attempts, then OPEN "261-flow").
- WHAT THE PLANTING DOES TO A FILM, SAID: it changes one line's text (flow, part) or one graphic (ladder, compare) of the offline film AFTER the voice
  is made; offline the voice is a tone, so nothing is heard wrong, but any other check that reads that line may move. That is a risk of the WALK, not
  of the build: no film without the flag is touched, and a film another check holds is reported by its own `problems` line.
- DOUBT 5 (the four templates are not a part of every block): approved as designed. `proving/` is not this row's to change; the planted tests stand
  in every block; the walk is a measurement at the batch's turn. If the owner's word ever opens the block file, the flag and the judge are what the
  part calls.

### STEP 9 (L4) AND MISS 279 - COVERED; nothing to change
- 02 item 123 as written (1122-1131): "the house-kit templates are a lasting use of the credit"; "The stick-figure look is treated as a crowded
  template, never our house look". The triage's third word is "free-written scene".
- THE HOUSE KIT: the kit is DRAWN's accepted code; L4 makes its accent ONE across the Short and the long video. In the tree: `drawn.PALETTE["b"]` is
  (255, 190, 70); `shorts2.py` holds "D7FF" three times and "(255, 214, 0)" once, and no test pins either (searched). `_accent()` gives the ASS colour
  in the eight-digit form the file already uses. Test 20's source scan catches LB-28 (the literal typed back). YES.
- THE STICK-FIGURE LOOK: a reason, not a step - and the reason is true of the memo I read: nothing in the batch draws a figure, the "you" figure is
  refused in both research parts, the judge is told to judge direction and never style. YES.
- THE FREE-WRITTEN SCENE: not in this batch, handed to B8's designer by name (the check list's hand-over 1). That is a hand-over INSIDE the build, not
  a cut - but it holds only if row F-B8 carries it: FOR THE COORDINATOR, doubt (c) below.

### THE NINE MATRIX ROWS - RIGHT IN SUBSTANCE; change 4
### THE LB-9 PAIR - RIGHT; change 3
### C4 TO C12 - change 5

### THE DESIGNER's OTHER MARKED ADDITIONS (read in lines 196-361)
- FC-2 and FC-3 stay (ruled above). FC-2's cost is said in the memo itself ("weighs 25 times an elephant" is refused too: refusing is free).
- THE THREE SEED ITEMS: each says what its step's code does, no more (the first matches A0a/A0b's rules as the steps name them and FC-3's narrower
  words on the compare's badge; the second names both checks and the bound on a run of holds; the third names the shape, the loud frames, his lock).
  Their evidence types are the seed file's own. Approved; the loader's clause in the bracket is right.
- STEP 8's TWO R16 ROWS (doubt 10): approved - a row is typed in the step whose code first makes it true.
- THE PLACES TODAY: spot-checked where I read the tree - `tools/sweep.py` 100, 131, 226, 233, 348-349, 403; `shorts2.py`'s literals;
  `tests/test_v12_inside.py` 712: as the table says. ONE LINE OFF: the table's `tools/rehearsal.py` "148-152" and "155" are 149-152 and 156 today
  (the words decide, as the memo says; step 3's three find lines each stand once).

## THE TEN QUESTIONS OF 5.4, FOR THE PARTS NEW OR CHANGED SINCE THE REVIEW OF RECORD (yes / no, one line of evidence)
1. Every part serves a viewer or the scoreboard? YES - A0c makes the block's evidence line true (a judge's words under its own label); A0d shows that
   four of the five diagrams a viewer can meet are drawable on the whole path; L4 is one accent a viewer sees; C8 to C10 keep money and pins honest.
2. Every word of the owner honoured? YES for 123's three binds (above) and 182 (unchanged); 238 ("nothing cut") holds only if C11/C12 and the
   free-written scene are carried by the rows named - doubts (a) and (c).
3. Every rule enforceable as written? YES after changes 1 and 2 (a planting that raised; a break caught only by a crash) and 3 (a break nothing caught).
4. A model's opinion as a gate? Unchanged since the review of record (his order, item 182); nothing new adds one.
5. On the finished file; both kinds of pairs? YES - `drawn_template_of` reads both drawn checks and the film's own record of what was SHOWN
   (`scenes.feature` with the shown units); its test plants a good film, another template and a failed check.
6. Money: a line, inside the cap? YES after change 5 (C8: the identity judge is a line; C9: booked to the film). OPEN for the day he opens the arm:
   the bound of Rs 800 - written into the block. The older gap (C11/C12) is named, not closed: doubt (a).
7. Reuse? YES - the sweep's own flag form, `drawn_of`, the offline writer's own flow, C7's own words, the matrix's own form.
8. Older pins named? YES after change 5 (C10's stand-in; the three-argument stand-in of `test_v12_owner.py` that must NOT move).
9. The worst video still let through by the new parts: none is added - steps 3 and 4 change no film without the flag. The worst WRONG WORD: a walk
   read as "all five drawn" when a run was held before its upload - change 6.
10. For the pilot, written down? YES - the walk's results and any OPEN "261-<template>"; the identity call's real price before the restyle opens.

## THE THREE PLACES I ATTACKED HARDEST
1. STEP 4's CODE AS A TYPIST WOULD TYPE IT - copied and run: 4 plantings x the memo's line, the corrected line, AB-22 and AB-23; the judge with and
   without AB-21; step 3's test on the file today, typed, and under AB-20. FOUND: change 1 (a TypeError), change 2 (a crash instead of a verdict).
2. THE NINE ROWS NOBODY HAD READ - every break B-1 to B-28 walked from the Opus memo's own list and F-10 to F-13 into its row, every function name
   checked against the tree, and the matrix test's own regular expression read. FOUND: change 4 (two cells; a form the test does not read).
3. WHAT THE REBUILD COULD TYPE AWAY - LB-9 by arithmetic on every pair of test 3; C4 to C12 line by line against what is still on disk. FOUND:
   change 3 (the pair stood where the memo's own rule overruled it), change 5 (seven corrections join; two cannot).

## WHAT STANDS ON ANOTHER READER's EYE, NOT MINE
- THE 566 LINES KEPT WORD FOR WORD stand on the review of record (R21) and T10; I read of them only the lines named at the top.
- THE BYTE-FOR-BYTE REBUILD stands on the designer's script (check list, section 2); I did not re-run the clerks' scripts.
- THE OTHER 84 BREAKS were NOT walked against their tests by arithmetic (the designer's doubt 3). I walked LB-9, LB-28, AB-20 to AB-23 and, by
  reading, the 28 B breaks into their rows. A walk of the LB list is the finisher's own act (A5 (2)) - it is worth saying so in its brief.
- A0d AGAINST A0a AND A0b is by reading, not by a run: the first builder's run of step 4's tests after steps 1 and 2 decides.
- THE WALK OF FOUR PRODUCTIONS, TO VERIFY 1, 10, 11, 12 and the Opus memo's TO VERIFY 1: not run by anyone yet (the check list's section 7).

## FOR THE COORDINATOR (none is a question to the owner)
(a) C11 AND C12 ARE OWED AND HAVE NO ROW. Their text is lost with the patch; only headlines stand (`drawnb_corrections_C1-C7.md` 131-163). A row must
    write them again (a small design, Fable) and they are typed as a step after B1 with a review of their own - OPEN "DRAWN-b-C12" until then.
(b) TWELVE STEPS, AND SEVEN MORE BREAKS: the typing is the plan's ten steps plus A0c (three lines, one test) and A0d (about 60 lines, two tests);
    B1 and B2 each gain the corrections' tests. The clock for DRAWN-b's typing should count it.
(c) THE FREE-WRITTEN SCENE (miss 279's third part) is closed here only by the hand-over to row F-B8: that row's brief must name it (P-F, P31, P3,
    open issue 259).
(d) THE OPUS MEMO's LOST TAIL: its TO VERIFY 5 is quoted nowhere; its PINS AND PLACES are replaced by the pack's `PLACES_DRAWN_B.md`; its nine rows
    by the designer's, now read (change 4). If a whole copy is ever found, its rows 1 to 9 are compared with these, not pasted over them.
(e) THE CHECK LIST's HAND-OVER 3 says "90 breaks": with change 5 the U1 APPLIER carries 97 (AB 23, LB 39, B 35).

## REVIEW_DRAWN-b_2.md - DRAWN-b, round 2 (word for word)

VERDICT: APPROVED (the memo DESIGN_DRAWN-b.md, round 2) - BUT RULINGS_U1b.md PART 3 (C11, C12): CHANGES REQUIRED, section C; that one step is not typed before its six edits are in
# REVIEW_DRAWN-b_2 - round 2 of the design review of DRAWN-b, and the FIRST review of RULINGS_U1b.md PART 3 (row R-FOLD-U1 of SUNDAY_PLAN_29NOV.md, 6c line 3)
WHO: the design reviewer of row R-FOLD-U1, Fable 5.2 High; I wrote nothing of the memo, of REVIEW_DRAWN-b.md, of the fold or of RULINGS_U1b.md.
Thu 26 Nov 2026, 19:19 UTC (`date -u`, read in this pass). THE MEMO CHECKED: `DESIGN_DRAWN-b.md`, 277,124 bytes, sha256 0064781c...11a1 - equal to
FOLD_U1_REPORT.md's AFTER line. READ: FOLD_U1_REPORT.md whole; REVIEW_DRAWN-b.md lines 29-116 (the six changes); of the memo ONLY what my script
printed around each edit and five greps; RULINGS_U1b.md lines 158-275 (PART 3 to the end); the headlines `DRAWN_b_typed_ahead_patches\
drawnb_corrections_C1-C7.md` 131-163. CODE at 8edef01: `whatifs/living.py` 30-74 and 104-111, `whatifs/sheets.py` 120-160, `whatifs/dash.py` 84-92,
`whatifs/costguard.py` (its `_line` and `lines` signatures, 10 and 51), `whatifs/core.py` 367, 702, 727, 734-736, and every line of `whatifs/` that
reads `rows("Character_Sheets")` (17 places, as the search printed them). RUN: two read-only scripts of my own and one line of python (a float
floor-divided by 0.0). No test, no pipeline run; NOTES\HOLD_TESTS absent before each run. Nothing of the repo, of `proving/` or of STATE.json was
touched; nothing committed.

## A. THE SEVENTEEN EDITS OF REVIEW_DRAWN-b.md - MY OWN REPLAY, NOT THE REPORT'S
METHOD: the script cut every FIND and REPLACE from REVIEW_DRAWN-b.md by its line (never retyped) and counted each in the memo as EXACT text.
| change | the new text | the old text | at line | the place |
|---|---|---|---|---|
| 1 | twice; the whole code line `SCN.ask = lambda ep_, wanted: {**real_ask(ep_, wanted), i: part}` twice | gone | 242, 293 | `plant_template`'s block and AB-23 - sound |
| 2 | once | gone | 293 | AB-21, first of the three breaks - sound |
| 3-a | once | gone | 791 | test 3 (i), before (j) - sound |
| 3-b | once | gone | 196 | sound |
| 4-form | once | gone | 349 | the sentence above the nine rows - sound |
| 4-row2, -row4, -row7, -row8 | once each | gone | 353, 355, 358, 359 | each in its own row - sound |
| 5-block (the review's lines 88-97 as one block, exact) | once | - | 314-323 | after the FC-3 line (312) - RULED SOUND (B) |
| 5-share, 5-all97 | once each | gone | 194, 196 | sound; one line begins `BREAKS SHARE:` |
| 5-step11, 5-step12, 5-cells, 5-cost | once each | gone | 302, 303 | sound |
| 6 | once, right after `never a skipped test.` | - | 294 | the end of THE WALK ITSELF's paragraph - sound |
THE COUNTS ADD UP: step 11's twelve (B-1 to B-8, B-21, B-29, B-30, B-35) + step 12's 23 (B-9 to B-20, B-22 to B-28, B-31 to B-34) = 35; 23 + 39 + 35 = 97.
RESULT: all seventeen are in, word for word, each in a sound place.

## B. THE FOLDER'S OWN DOUBT, RULED
THE EMPTY LINE BEFORE CHANGE 5's BLOCK: STANDS, AND IS RIGHT. The line above (312) is a list item ("- FC-3 ..."); without an empty line the block's
first line "MF - THE CORRECTIONS OF 20 Nov ..." would read as the tail of FC-3. With it the block is "a block of its own", as the review orders,
and stands as the memo's other "MF - " blocks do (an empty line follows it too, before "MF - THE THREE SEED ITEMS").
SAID, NOT REQUIRED: (i) the Opus memo's own file list still says "`core.py` (five cells)" (line 1109): line 196 as changed says the marked block
wins, and the block's B-33 names the sixth cell - no typist is left to choose. (ii) B-35 stands in no matrix row (it is the moved pin of an older
test, in the break list all the same): the review of record ordered it so.

## C. RULINGS_U1b.md PART 3 (C11 AND C12, WRITTEN AGAIN FROM THE HEADLINES) - FIRST REVIEW: CHANGES REQUIRED, SIX EDITS
(REVIEW_DRAWN-b change 5 ordered "a review of its own"; this is it. Each FIND below was counted by script in RULINGS_U1b.md: EXACTLY ONCE, with
whitespace runs matching any whitespace run - the file wraps its lines. REPLACE = the find becomes the text.)

WHAT HOLDS, CHECKED BY ME
- AGAINST THE HEADLINES (131-163): `variant_room`'s rule is the headline's sentence; test c12b (1) to (3), B-C12-2's find, the 14 files and the nine
  money pins are the headline's. The default "2" of LIVING_VARIANT_TRIES is the lost C11's own: 2 x 6.633 + 2 x 40 = Rs 93.27 is the very sum the
  first lost run measured on every estimate.
- AGAINST THE CODE: lines 46, 48-49, 59-61, 69-70 of `living.py` are as PART 3 reads them. `cap_room()`'s formula is today's rule exactly ("buy
  while spent is not over the cap": with n rows the buys still allowed are floor((cap - spent) / price) + 1). `variants` has ONE caller
  (`living.py` 109) and it takes two values. B1 puts LIVING_CHARACTERS_ON back to "TRUE" (memo line 302), so test c12's "at the defaults" holds.
- A ROW WITH NO FILE IS SAFE TODAY: of the 17 places that read Character_Sheets, each line I saw passes a "+" row with status "REJECTED" or "TRIED"
  and no file by: `_sheet_rows`, `specials` 77, `sheets` 163 (LOCKED and a file); `used()` (a file); `auto_lock`, APPROVE and the dashboard card
  (a DRAFT status); `episode.py` 904 (LOCKED); REDO (its pattern `[a-z]+` cannot name a "+" expression); the masters' readers (expression "master"). `update_where` is keyed
  by hash only for DRAFT rows, so several rows with the hash "<char><expr>+<kind>" are never updated. NOT OPENED: the bodies under `dash.py` 400 and
  `sheets.py` 55 and 89 (their `have` by hash) - PART 3's own order (the typist's locator pass names every reader in TYPED) covers them.

THE SIX EDITS
1. `cap_room()` DIVIDES BY THE PRICE AND THE PRICE CAN BE 0 (rule 4). Line 48 today guards the rate (`S("USD_INR", float) or 92.0`) and never
   divides. PART 3 drops the guard and adds `// price`: with PRICE_GEM_IMAGE_USD or USD_INR at 0 or empty that is `ZeroDivisionError: float floor
   division by zero` (run by me) - in `variants` outside its `try`, and through `variant_room()` in `costguard.lines`, that is in EVERY estimate.
   - FIND: ``with `price` = PRICE_GEM_IMAGE_USD x USD_INR and `spent` ``
   - REPLACE BY: ``with `price` = PRICE_GEM_IMAGE_USD x (USD_INR or 92.0 - line 48's own guard, kept); when `price` is 0 or less (a free picture) it returns 999 and divides nothing (today's line never stops a free picture either; the film's count and the missing slots still bound it); else with `spent` ``
   - FIND: ``(6) an empty `variant_tries.txt` -> nothing asked.``
   - REPLACE BY: ``(6) a new film whose `variant_tries.txt` is planted empty -> nothing asked; (7) PRICE_GEM_IMAGE_USD "0", the stub of (1), a new film: `LV.cap_room()` is 999 and raises nothing, and two calls of `variants` ask 2 pictures and no more.``
2. RULE 2's "WRITTEN BEFORE THE PICTURE CALL, SO A FAILED CALL IS COUNTED" HAS NO TEST, AND TEST (5) CANNOT RUN AS WORDED. After (3) the cap cell
   is "10" (nothing can be asked), and one `variants` call asks BOTH kinds, so a raising picture call leaves two rows, not one.
   - FIND: ``(5) the picture call raising -> one row ("TRIED", ""), counted like the others;``
   - REPLACE BY: ``(5) the cap cell back at "150", a NEW film "EPC11b", the picture call raising: `LV.variants(char, "neutral", base, "EPC11b")` -> (None, None), two more "+" rows, each ("TRIED", ""), the picture asked exactly 2 times more, and a second call in that film asks nothing (the failed calls are in the film's count - rule 2's "written BEFORE");``
3. THE BREAKS: two name the wrong place of the test, one doubles another's assert, and rule 2's order has none. As worded B-C11-2 is caught at
   (1)'s second call (not at (2)), and B-C11-4 (the append out) fails the same row assert of (1) as B-C11-3 and never reaches (3) - so nothing
   proves that the cap counts a row with no file.
   - FIND: ``BREAKS (the headline's three, plus one): B-C11-1 the film's count not read (4 asked, caught at (1)); B-C11-2 the count's `>=` made `>` (a third asked, caught at (2)); B-C11-3 "REJECTED" made "TRIED" (caught at (1)); B-C11-4 the REJECTED row's append out (caught at (3)).``
   - REPLACE BY: ``BREAKS (the headline's three, plus two; each find is the typist's own line, quoted exactly, standing ONCE in the file): B-C11-1 the film's count not read (4 asked, caught at (1)); B-C11-2 the count's `>=` made `>` (a third asked, caught at (1)'s second call); B-C11-3 "REJECTED" made "TRIED" (caught at (1)); B-C11-4 in `cap_room` the sum made to count only the rows that HAVE a file (caught at (3): the new film asks); B-C11-5 the count's write moved to after the picture call (caught at (5): the second call asks again).``
4. THE PIN IS NAMED BY A LITERAL OF THE LOST COPY. "EPB13" stands nowhere in `DESIGN_DRAWN-b.md` (counted: 0) and `tests/test_v12_drawn_b.py` is
   not in the tree: step 11 types test 3 from the memo, with a film id of its own.
   - FIND: ``asks two arts' variants in ONE film "EPB13" (4 pictures, over the film's 2): each art gets its own film, `f"EPB13{w}"`.``
   - REPLACE BY: ``is typed by step 11 from the memo (the memo names no film id; "EPB13" was the lost copy's). Where it asks two arts' variants in ONE film (4 pictures, over the film's 2), each art gets a film of its own: the test's film id with the art's own word added. If step 11's test 3 already uses one film an art, nothing moves and TYPED says so.``
5. THE TWO LINES LEAVE THE TYPIST TWO THINGS TO DECIDE (C12, rule 2): where they hang, and their words. "Directly after C8's statement, in C8's
   form" can be typed under C8's `if rr_ is not None:` - then no line stands while the restyle is off; and the `what` of each line stands in angle brackets.
   - FIND: ``two lines appended directly after C8's `restyle_identity` statement, in C8's form:``
   - REPLACE BY: ``two lines appended directly after C8's `restyle_identity` statement, in C8's form but at `lines`' own indentation under an `if n > 0:` of their own - NEVER under C8's `if rr_ is not None:` (the restyle is off at the launch; these lines do not hang on it) - each with the `what` given here, typed as it stands:``
   - FIND: ``<the talking cast's blink and mouth pictures still to buy>``
   - REPLACE BY: ``"the talking cast: blink and mouth pictures still to buy"``
   - FIND: ``<the identity check of each of them>``
   - REPLACE BY: ``"the talking cast: the identity check of each blink or mouth picture"``
6. THE MATRIX ROW IS IN THE FORM NOTHING READS, AND THE BREAKS HAVE NO HOME (REVIEW_DRAWN-b change 4: `tests/test_v111_enforce.py` 98-110 checks
   only `fn:<module>.<function>` and `contract:<check>`; a bare name in backticks is a row nothing checks). The row's words also say "twice a
   film" where the rule is the cell.
   - FIND: ``"A blink or mouth picture that failed is counted by its cap, asked at most twice a film, and is a line of the estimate | `living.variants`, `living.variant_room`, `costguard.lines` | test_c11, test_c12, test_c12b; B-C11-1 to -4, B-C12, B-C12-2".``
   - REPLACE BY: ``"A film asks at most LIVING_VARIANT_TRIES blink or mouth pictures; a rejected or failed one is a counted row of the variants' lifetime cap; the pictures still to buy and their identity check are lines of the estimate | `fn:whatifs.living.variants` `fn:whatifs.living.cap_room` `fn:whatifs.living.variant_room` `fn:whatifs.costguard.lines` | test_c11, test_c12, test_c12b; B-C11-1 to -5, B-C12, B-C12-2" (the references in the file's own form, REVIEW_DRAWN-b change 4). THE SEVEN BREAKS join DRAWN-b's own break list under these ids, after B-35: the batch's count is then 97 + 7 = 104.``
   FOR THE COORDINATOR, NOT DECIDED BY ME (I do not know what reads the line): whether `DESIGN_DRAWN-b.md` line 194 then moves to 104. If it does,
   the two edits are (each find counted once in the memo): ``BREAKS SHARE: 97 (`` -> ``BREAKS SHARE: 104 (`` and ``B-1 to B-35: 35)`` ->
   ``B-1 to B-35: 35; B-C11-1 to -5, B-C12, B-C12-2: 7)``.

SAID, NOT REQUIRED (for CR-DRAWN-b and the pilot; none blocks)
- WHAT A VIEWER SEES: a film asks at most 2 pictures, so in the first films after he locks a sheet himself ONE expression of ONE character blinks
  and talks; the other cutaways show the still as they do today without variants. About three films a character at the default expressions. The
  cell LIVING_VARIANT_TRIES is the lever; the 2 is the lost C11's.
- THE Rs 40 UNIT IS A BOUND AND IT MOVES OTHER MONEY: from his first own Approve of a sheet a long film's estimate gains up to Rs 93.27 until the
  slots are made; in the lost first run that sum moved the hero clip's rate and the month's free room (headline 157-163). It errs to the careful
  side (less spent, never more). PART 3's own doubt names the cure: one identity call measured and RESTYLE_ID_EST_INR set BEFORE he can lock a
  first sheet. The first real sheets run makes such calls before any sheet card reaches him - the measured price is in Cost_Log by then.
- Nothing of the film's count (the folder made, the file read or written) may raise out of `variants`: its cap test stands outside the `try` and
  `living.render` calls it bare (109). `costguard` imports `living` inside `lines`, not at the top (it pulls numpy). `variant_room` hands
  `_sheet_rows` the character in capitals (line 13 compares so). A Short's estimate holds neither line. If the Sheet does not answer,
  `variant_room` raises into `lines` as every other read does - it must not answer 0 silently.
- STILL OPEN, AS PART 3 SAYS ITSELF: a variant the judge did not answer (`sc` None) is accepted as made - the audit's line, nothing typed.

THE TEN QUESTIONS OF 5.4, FOR PART 3 (yes / no, one line)
1. Serves a viewer or the scoreboard? YES - the money side of the talking cast; it changes no frame but which films get the blink first.
2. His words? YES - item 146 (every paid call a line), item 238 (nothing cut: C11 and C12 are back in this build), item 169 (nothing asked of him).
3. Enforceable as written? NO until edits 1 to 3 (a crash at price 0; a rule with no test; a break that proves nothing new) - YES after.
4. A model's opinion as a gate? Unchanged: the identity judge of line 60, as accepted; nothing new.
5. On the finished file, measured pairs? Not touched. LIVING_MIN_IDENTITY 7 has no measured pairs of its own (as F318's floor): the pilot's.
6. Money a line, inside the cap? YES - that is the step: two lines, a lifetime cap that now counts every attempt, a film's count.
7. Reuse? YES - C6's and C7's file form, C8's line form and its price cell, `_sheet_rows`.
8. Older pins named? YES after edit 4 - the nine money pins must stay green and unmoved; the 14-file run is named; test 3's move is worded for the test as it will be typed.
9. The worst that still gets through: an unjudged variant accepted as made (named open); a picture bought, judged good, lost at the upload, bought again in a later film - bounded by the cap.
10. Only reality answers: the price of one identity call; whether the judge rejects real blink pictures often enough to matter (the REJECTED rows will say).

## FOR THE COORDINATOR (none is a question to the owner)
- THE MEMO: approved as it stands on disk (sha256 above). Steps 1 to 12 do not wait for anything in section C.
- PART 3: the six edits go into `RULINGS_U1b.md` by script (each find once), by the row that owns that file; T-DRAWNb section 3 types C11 and C12
  as its LAST step only from the edited PART 3. The edits are checkable by count; whether a further reader is owed is the plan's rule, not mine.
- The launch pack's line beside the restyle's: "RESTYLE_ID_EST_INR is set from the first measured identity call (Cost_Log, the first real sheets
  run) before his first sheet card is sent" - it is also the unit of `living_identity`.
- NOTES_REVIEWER_DRAWN-b's note 13 is answered: a diff that holds `living_variants`, `living_identity`, `variant_room` is no longer a finding BY
  ITSELF; it is read against PART 3 as edited.

## NOT READ
The memo outside the lines named above. RULINGS_U1b.md PARTS 1 and 2. The headlines file outside 131-163. `costguard.lines`' body, `sheets.py`
1-119, `dash.py` 400-405. No test was run: every "caught at" above is from reading the rule against the test as worded.

## REVIEW_F318.md - F318, round 1 (word for word)

VERDICT: CHANGES REQUIRED
# REVIEW_F318 - design review of N\DESIGN_F318.md (row R-318, Fable 5.2 High; not the designer's lane)

Written 26 Nov 2026 19:05 UTC (`date -u` read at 18:56 in the same pass). Checkout read: reality-engine at 8edef01, clean. Nothing was run
(no python, no pytest, no ffmpeg; NOTES\HOLD_TESTS was absent when looked). There is no N\PACK_F318.md; the pack named by the row is the
memo, triage line 318 and N\PACK_CHECKLISTS.md (5.4), and I read those plus the S0 lines the memo quotes.

The design is sound and C is the right choice. Eight changes, all small, all with the exact text. Changes 2, 3 and 5 touch lines of
section 1 that T-318-1 is typing now: SECTION 2 TYPES THEM as corrections (each is a replace of the quoted line). No change cuts anything.

THE FORM CHECKS OF THE ROLE CARD: Step 1 holds 10 https addresses (5 opened and dated by the designer; I opened source 2 myself - the page
says "Submitted on 23 Apr 2026" and the numbers quoted are in its abstract). Step 2 holds four lettered designs A-D and the word ORIGINAL
(C). The DEPENDS ON line and the BREAKS SHARE line are there. Triage line 318 (DEFERRED_TRIAGE.md:320) is quoted word for word.

## THE NUMBERED CHANGES (the memo must ...)

### 1. The Remake tap and the low score must be on the DASHBOARD too (his item 149: "EVERYTHING ON WHATSAPP AND THE DASHBOARD, BOTH ... MY INPUTS TAKEN FROM EITHER")
Step 11 says "the card's own button is on both screens". It is not: TWO_SCREENS_ON is TRUE by default (`core.py` 1219), and then
`dash._docket` skips every `sheets_review` row (`dash.py` 57) and shows its own card (86-93) whose "Redo" only answers with a pointer to an
e-mail link (404-405). So on one of his two screens the new sentence and the new tap do not exist. Text to change:

(a) In step 11 delete the words `; the dashboard verb `REDOSHEETS` (`dash.py` 404-405) stays a pointer - the card's own button is on both screens`.

(b) Add step 8b after step 8:

8b. `whatifs/dash.py` - the same fact and the same tap on the dashboard (item 149).
   `route`, the REDOSHEETS branch (404-405) becomes:

        if head == "REDOSHEETS" and len(parts) == 2:
            if S("MASTER_FLOOR_ON", bool) and any(r.get("character") == parts[1] and r.get("expression") == "master" and str(r.get("status") or "").startswith("DRAFT") for r in store().rows("Character_Sheets")):
                from whatifs import sheets as SH                                 # v12 F318: his Redo on a master's draft is the card's Remake - one road (sheets.decide)
                return True, str(SH.decide(f"REDO SHEET {parts[1]} master"))
            return False, "Redo one expression with the email link 'REDO SHEET <NAME> <expression>' (lifetime image cap applies)"

   a new function above `_docket`:

    def _low_master(ch):
        """v12 F318: the dashboard's words for a master draft the judge scored under the floor - the same fact the masters' card says."""
        if not S("MASTER_FLOOR_ON", bool): return ""
        from whatifs import sheets as SH
        floor = S("MASTER_MIN_IDENTITY", float)
        for r in store().rows("Character_Sheets"):
            if r.get("character") == ch and r.get("expression") == "master" and str(r.get("status") or "").startswith("DRAFT"):
                sc = SH.status_score(r.get("status"))
                if sc is not None and sc < floor: return f" The judge scored this master {sc:.0f}/10 against your portrait, under {floor:.0f}/10: Redo remakes it."
        return ""

   and in `_docket` (line 91) the card's why becomes
   `"why": "Locked portraits let this character appear on thumbnails and in scenes, always the same face." + _low_master(ch),`
   TEST T16 `test_the_dashboard_says_a_low_master_and_its_redo_remakes_it` - a GRIMM master row "DRAFT (identity 6/10)" with a file: the
   card "sheets-GRIMM" of `dash._docket()` has the S0 why followed by " The judge scored this master 6/10 against your portrait, under
   7/10: Redo remakes it."; a "DRAFT (identity 7/10)" row and a plain "DRAFT" row: the S0 why word for word; `dash.route("REDOSHEETS|GRIMM")`
   is (True, a reply holding "has been started"), the row is REDO and `BLD.dispatch` got ("sheets.yml", {}); with only expression drafts of
   GRIMM, with only a LOCKED master, and with MASTER_FLOOR_ON FALSE: (False, the S0 pointer), no row changed, nothing dispatched.
   BREAK F318-52: in `route` the words `r.get("expression") == "master" and ` removed from the `any(...)`; T16 must fail (expression
   drafts only would answer True). BREAK F318-53: in `_low_master` `sc < floor` -> `sc <= floor`; T16 must fail (the 7/10 row).
   SWITCH: MASTER_FLOOR_ON (FALSE = the S0 pointer and the S0 why). MATRIX: step 10. COST: none (the run it starts is step 5's).
   OLDER TESTS: none pins the REDOSHEETS reply or the card's why (grep of tests/, tools/, docs/CURRENT: 0 places).

(c) Step 10's row becomes (first words unchanged, so T14 stands):
`| A LOW-SCORED CHARACTER MASTER IS REMADE BEFORE IT CAN LOCK (F318; triage 318, R1-104 (3)): against a portrait he locked the judge looks both ways and the lower answer counts; under MASTER_MIN_IDENTITY the master is remade in the same run, at most MASTER_REMAKES_MAX times, only from the lifetime cap's spare and only when the month's money says yes; every attempt is a counted row; the best attempt is his draft, its card and the dashboard say so, and his one tap (Remake on the card, Redo on the dashboard) clears the live picture and starts the run | `fn:whatifs.sheets.master_score` `fn:whatifs.sheets.masters` `fn:whatifs.sheets.sheets_owed` `fn:whatifs.sheets.decide` `fn:whatifs.sheets.start_sheets_run` `fn:whatifs.dash._low_master` `fn:whatifs.dash.route` | built into the sheets run + tests |`

(d) The DEPENDS ON line gains, before its closing bracket: `; step 8b types `whatifs/dash.py` 86-93 and 404-405 and one new function there - S0 lines of B-OWNER`.
(For the coordinator: dash.py is a file the memo did not name before; no other open row should type those lines at the same time.)

### 2. The cap must be asked BEFORE the portrait is fetched, as at S0
At S0 `if used() >= cap ...: break` (line 59) comes before `SP._portrait` (60). The typed shape fetches the portrait first, and
`_portrait` draws a PAID picture when the character has no LOCKED row or the Drive download fails (`specials.py` 80-89). A cap set low
to stop spending would then still pay for portraits. In THE TYPED SHAPE, after the line `if limit and made >= limit: break`, add:

        if used() >= cap and not master_tries(p["hash"], st.rows("Character_Sheets")): break      # as at S0 the cap is asked BEFORE the portrait (it can draw a paid picture); a round already begun still ends below

and replace the two lines

            if k == 0:
                if used() >= cap: break

with the one line

            if k == 0: pass                                                       # the first picture: the cap was asked above, before the portrait

(the next line `elif k > more: why = "no remake left"` and every line after it stay as written.)
T5 gains: "with the cap already full (= `used()`): no picture at all AND `SP._portrait` is never called".
Break 31 becomes: `| 31 | masters | the line `if used() >= cap and not master_tries(p["hash"], st.rows("Character_Sheets")): break` removed | T5 (cap already full: a picture is bought) |`.

### 3. The paid loop must also end by its own count
The `while` ends only through what a re-read of the tab shows (`k`). Every exit was traced and holds today (`SheetStore.append` raises
on a failed write, `_all` has no cache), but a loop that buys pictures should not hang on that alone - S0's `run` counts locally
(`base + made`). In THE TYPED SHAPE replace the line

        while not kept and not why:

with the two lines

        for _ in range(more + 1):                                                 # a paid loop also ends by its own count, never only by a re-read of the tab
            if kept or why: break

Nothing else in the body changes: a round that ends by the count is promoted by the block below, and its `why or "no remake left"`
already gives the words. (Traced by me against T1-T8, T11, T12 and breaks 05, 18, 41, 42: same results, all still end.)
Break 26's test changes: `| 26 | masters | `elif k > more:` -> `elif k > more + 1:` | T8 (three seeded: one more is bought) |`.
NEW TEST T17 `test_a_round_ends_by_its_own_count_when_the_tab_does_not_show_the_new_rows` - `SH.master_tries` stubbed to answer [] always,
every score 3, default cells: exactly three pictures are bought (MASTER_REMAKES_MAX + 1), never a fourth.
NEW BREAK F318-54: `range(more + 1)` -> `range(more + 2)`; T17 must fail.

### 4. The card must say when a Remake takes a picture from the expression sheets
With the defaults the spare is 6 and the worst first run uses all 6. After that every Remake tap buys its first picture from the cap
(the spare rule guards only the tries after it), so one planned expression picture is never made - silently. Remake is the FIRST button.
In step 7, before the `NT.mail` call add the line
`spare_note = " (no spare picture is left: a remake takes one from the expression sheets)" if low and cap - used() - sheets_owed() < 1 else ""`
and in the new paragraph replace `Tap Remake to try again; left alone, {dflt}.</p>"` with `Tap Remake to try again{spare_note}; left alone, {dflt}.</p>"`.
T4 (default cells, spare left) keeps its sentence word for word. T5 gains: "in the first case (cap = `sheets_owed()` read before the run)
the card's sentence holds ' (no spare picture is left: a remake takes one from the expression sheets)'; T4's card does not hold it".
NEW BREAK F318-55: `sheets_owed() < 1 else ""` -> `sheets_owed() < 0 else ""`; T5 must fail.

### 5. The lower-of-two-looks is a NEW measure with no measured pairs: both answers must be kept, and the pilot's questions written down (5.4 questions 5 and 10)
The floor 7 is borrowed from `living.py`'s one look; the turned look ("is the second the SAME character as the first, restyled", with
his portrait second) may run lower by itself, and only the lower answer is stored. It gates no lock and no video, so it may stand - but
the memo must make it readable. In THE TYPED SHAPE, `master_score` gains one line between `looks = [...]` and `return ...`:

        log(f"master {who}: identity looks {looks}")                              # both answers stay in the run's log: the pilot reads whether the turned look runs lower

(breaks 03, 15, 16, 17 quote other text and stand.) And step 11 gains this paragraph at its end:
`OPEN FOR THE PILOT (only a real run answers; nothing waits on it and nothing is asked of him): (a) whether the turned look runs lower than the forward look on real masters - the run's log line "identity looks"; if it does on every master the lower-of-two is stricter than the 7 it borrowed, and MASTER_MIN_IDENTITY is the cell to move; (b) which try stands - the kept row's `prompt` says whether the plan's text or the "retry" text made it (the retry text rests on one undated source); (c) the floor has no measured good and bad pairs of its own - it buys at most two pictures and words on a card, it gates no lock and no video; (d) the real cost of a round, read from Cost_Log episode "SHEETS" (the Rs 43 is from price cells).`

### 6. T9's hash is wrong by one round
T9 seeds "an old REDO row" and then taps: that is TWO rows "<h>-redo-...", so `master_round` is 2, not 1. Replace in T9
`rows in this order [an old REDO row, try0 REJECTED, the live DRAFT, try2 REJECTED]` with
`rows in this order [an old REDO row with hash "<h>-redo-2026-11-01T00:00", "<h>-r1-try0" REJECTED, the live "<h>" DRAFT, "<h>-r1-try2" REJECTED]`
and `the next `masters()` writes "<h>-r1-try0" and may buy three again` with
`the next `masters()` writes "<h>-r2-try0" (two REDO rows = round 2) and may buy three again`.

### 7. The TYPING ORDER line must say what section 1 cannot show
T4, T5, T6, T7 and T12 assert the card's words, and the card is step 7 (section 2); `start_sheets_run` sits in THE TYPED SHAPE but its
only caller is step 8 (a function typed ahead of its caller is red on `tests/test_v12_b0b.py` 250). Replace the TYPING ORDER line with:
`TYPING ORDER: section 1 = steps 1-6 with tests T1-T8, T11-T13; section 2 = the review's changes 2, 3 and 5 to section 1's lines, then steps 7-10 and 8b with T9, T10, T14-T17 and the breaks file. `start_sheets_run` is step 8's and is typed with its caller. The card's words that T4, T5, T6, T7 and T12 assert are step 7's: those five are green only after section 2, and no one judges section 1 by them alone.`

### 8. The BREAKS SHARE line and the count
`BREAKS SHARE: 50` becomes `BREAKS SHARE: 54` (the 50, plus F318-52, -53, -54, -55 of changes 1, 3 and 4), and the sentence under the table
`(9 of the steps + these 41 = 50.` becomes `(9 of the steps + these 41 + the review's 4 (52-55) = 54.`

## THE DESIGNER'S DOUBTS, ANSWERED
- BREAKS SHARE 50, not about 90: AGREED. I traced all 50 against the typed shape - each is one place and each named test fails on it
  (the only wrong test text is change 6). About 90 on about 80 typed lines would be padding. It is 54 after this review; the coordinator
  finds the rest of U1's 268 elsewhere.
- The second try's prompt (one undated vendor article): KEEP IT, breaks 13, 14, 32 stay. It is one try of three, the same judge picks
  the best by the same number so the kept master is never worse than try 1 by that measure, it invents no feature (T13), and no matrix row
  or test requires `char_lock` in every prompt (`test_v102.py` 139-146 only forbids invented words). Its worth is the pilot's (change 5 (b)).
- The dispatch token: CHECKED on the two jobs that take his tap. `whatsapp.yml` (permissions 7-9 `actions: write`; env 30, 35) and
  `dash.yml` (7-9; 27, 36) both hand GH_MERGE_TOKEN and GH_TOKEN = `github.token`; `builds._h` (8-9) takes the first that is set. Both
  can start `sheets.yml`, which takes no inputs (`sheets.yml` 3-4). The issue-title road (`preview.yml` 73) has GH_MERGE_TOKEN only; where
  it is refused the S0 reply is given and is true.
- About Rs 43 a round from price cells: accepted as said, "about" kept; 6 x 0.067 x 99 = Rs 39.80 and 15 looks are right. Change 5 (d).

## THE TEN QUESTIONS OF 5.4
1. Serves a viewer a layman could name? YES - a face that moved is not copied into every scene. Thinnest part: the retry text (kept, see above).
2. Honours every word of his that touches it? NO until change 1 (item 149: both screens). It keeps R1-104 (C) / row 34 (silence
   locks - T15), asks him nothing (one tap offered, silence works), keeps the card's kind and dedupe key (`test_v12_owner.py` 345, 1093).
3. Enforceable as written? YES - the lower of two looks, a floor, counts read from rows; 54 breaks, each with its test.
4. Taste judged by a cheap model, or a model's opinion gating a video? NO - the judge buys at most two pictures and picks the best of
   three by its own number; it locks nothing and holds nothing. His card and his silence decide, as ruled.
5. Judged on the finished file; measured pairs before a limit? The finished picture: yes. Measured pairs: NO - change 5 writes it down;
   it may stand because the limit gates nothing.
6. Money a line of `costguard.lines`? No new paid call and no new line: it is the existing `image_ref` item of episode "SHEETS", which
   belongs to no video (the memo's reason accepted). Bounded by MASTER_REMAKES_MAX, the spare and `governor.extras_allowed` (149-163);
   changes 2 and 3 close the two places where a paid call did not hang on those bounds.
7. Reuses what is there? YES - `builds.dispatch`, `governor.extras_allowed`, `notify.mail`, `identity_score`, `sheets.decide`.
8. Older pins named? YES, and read by me: `test_v12_owner.py` 266-275, 1086-1093, 1606-1622 (no LOCKED portrait or no portrait: not
   judged, they stand), `test_v102.py` 128-146, `fakes.py` 425-427 (no "score": the floor steps aside offline). Change 1 moves no pin.
9. The worst that still gets through: a master the judge scores 7 or more both ways although the face moved, or a best-of-three under
   the floor that he leaves alone - it locks after 72 h and is the face of every scene. Held only by his eye on the card (the ruling);
   the per-scene face check compares with the master, not with his portrait. Same as S0, made less likely.
10. What only reality answers, written for the pilot? NO until change 5.

## THE THREE PLACES ATTACKED HARDEST
- The paid loop: every exit traced by hand for k = 0..3, for a died run, a failed write, a governor no and each of breaks 05, 18, 26,
  37, 41, 42, 44. It ends in every case; changes 2 and 3 are fences, not repairs of a found hole. The spare rule's sum was checked on the
  default cells: 9 pictures for three masters and 31 still owed = 40.
- His tap's road: card -> `notify.answer` (385-387, the value keeps its lower-case "master") -> `preview.decide` (116-118) ->
  `sheets.decide`; a tapped card is ANSWERED, so the remade master's card is not swallowed by the dedupe key (`send` 176-177 looks at
  OPEN rows only). The dashboard road was the hole (change 1).
- The break table: all 50 traced; one test literal wrong (change 6); break 26 moves to T8 because of change 3.

## NOTED, NOT REQUIRED (for the code review and the pilot; none blocks)
- A REDO tapped when `used() >= cap` clears the live master and nothing can replace it. S0 behaviour of `decide`; not reachable from a
  fresh card (while masters are drafts no expression is made, so `used()` is far under the cap).
- Step 7's "`low` is empty when off" is not exact: T8's third case (a refused row left by a dead run, the switch FALSE) promotes it and
  the card carries the sentence and the button. True words, harmless; T7 must seed no refused row.
- When the Drive download of his portrait fails, `_portrait` draws a new picture and the score is taken against that. S0 fault.
- After a Redo on the dashboard the WhatsApp card of that day stays open with the old score (the dedupe returns the open row).
- `living.py`'s "+eyes" / "+mouth" rows have a file, so `used()` counts them and they lower the spare. S0.
- GitHub keeps one waiting run per `sheet-heavy` group; harmless, any run makes every missing master.

## REVIEW_F318_2.md - F318, round 2 (word for word)

VERDICT: APPROVED
# REVIEW_F318_2 - round 2 of the design review of F318 (row R-FOLD-U1 of SUNDAY_PLAN_29NOV.md, 6c line 3): are changes 1 to 8 of REVIEW_F318.md in the memo
WHO: the design reviewer of row R-FOLD-U1, Fable 5.2 High; I wrote nothing of the memo, of REVIEW_F318.md or of the fold. Thu 26 Nov 2026, 19:19 UTC
(`date -u`, read in this pass). THE MEMO CHECKED: `DESIGN_F318.md`, 38,826 bytes, sha256 0c05ab33...afa1 - equal to FOLD_U1_REPORT.md's AFTER line.
READ: FOLD_U1_REPORT.md whole; REVIEW_F318.md whole; of the memo ONLY what my script printed around each edit and lines 86, 120-150, 190-193,
200-204, 254-258, 286-290, 331-339. RUN: one read-only script of my own (no test, no pipeline; NOTES\HOLD_TESTS absent before each run). Nothing of
the repo, of `proving/` or of STATE.json was touched; nothing committed.

## A. THE TWENTY-THREE EDITS - MY OWN REPLAY
METHOD: every text was cut by script from REVIEW_F318.md by its line and counted in the memo as EXACT text (T17 and T5's second addition, which the
review wraps over two lines, with whitespace runs matching). The code lines of THE TYPED SHAPE were matched as WHOLE lines, indentation included.
| change | in the memo | at line | the place |
|---|---|---|---|
| 1 (a) the deleted words | 0 times left | step 11 | sound |
| 1 (b) step 8b, the review's lines 26-58 as one block | once, exact | 215-247 | after step 8's last line, before step 9 - sound |
| 1 (c) step 10's row | once; one row begins "| A LOW-SCORED" | 269 | sound |
| 1 (d) DEPENDS ON | once | 77 | before the closing bracket - sound |
| 2 the cap line | once, whole line | 127 | after `if limit and made >= limit: break`, BEFORE `SP._portrait` - sound (the change's whole point) |
| 2 the two lines -> one | old pair 0 times; new line once | 134 | sound |
| 2 T5 gains | once | 257 | sound |
| 2 break 31 | once; one row begins "| 31 | masters |" | 310 | sound |
| 3 the loop | `while not kept and not why:` 0 times; the two `for` lines once | 131-132 | sound |
| 3 break 26 | once; one row begins "| 26 | masters |" | 305 | sound |
| 3 T17 | once | 267 | step 9's list, after T15 - RULED SOUND (B) |
| 3 F318-54 | once | 192 | step 5, after F318-05 - RULED SOUND (B) |
| 4 the `spare_note` line | once | 204 | step 7 - RULED SOUND (B) |
| 4 the paragraph | once; the old ending 0 times | 204 | sound |
| 4 T5 gains | once | 257 | T5's end - RULED SOUND (B) |
| 4 F318-55 | once | 206 | step 7, after F318-07 - RULED SOUND (B) |
| 5 the log line | once, whole line | 93 | between `looks = [...]` and `return` - sound |
| 5 the pilot paragraph | once | 279 | a line of its own at step 11's end - RULED SOUND (B) |
| 6 T9's rows, T9's next round | once each; both old texts 0 times | 261 | sound |
| 7 TYPING ORDER | once; one line begins "TYPING ORDER:" | 86 | sound |
| 8 the share, the count | `BREAKS SHARE: 54` once, `50` gone; the count sentence once, the old gone | 78, 331 | sound |
RESULT: all twenty-three are in, word for word.

## B. THE FOLDER'S OWN DOUBTS, RULED (the review named the text, the folder chose the place)
1. T17 in step 9's list after T15: STANDS. Step 9 is the test file's list; the TYPING ORDER line (86) puts T17 in section 2 with T14 to T16.
   Traced against THE TYPED SHAPE as it stands (127-134): with `master_tries` answering [] always, `k` is 0 in every pass, each pass buys one
   picture, `range(more + 1)` ends it at three; `range(more + 2)` buys a fourth: T17 fails under F318-54.
2. F318-54 in step 5 after F318-05, F318-55 in step 7 after F318-07: STAND. That is the memo's own form for a step's own break, and the count
   sentence (331) names "the review's 4 (52-55)".
3. The `spare_note` sentence in step 7: STANDS, with one thing for the code review. The memo now reads: the paragraph's f-string (which holds
   `{spare_note}`), then "Before the `NT.mail` call add the line `spare_note = ...`". Both are the review's words. The name must be bound before
   the f-string that uses it is built - if the paragraph is built on a line before the `NT.mail` call, `spare_note` goes above THAT line. A wrong
   order is a NameError on the first low master, and T4 (the card's words) cannot be green with it; the note is carried to CR-318.
4. T5's second addition at T5's end: STANDS. Checked by arithmetic: in T5's first case the cap is `sheets_owed()` read before the run, one picture
   is made, so `cap - used() - sheets_owed()` is 0 or less (the helper's portrait row has a file too), under 1: the bracket is said. That T4's card does
   not hold it on the default cells is REVIEW_F318's own statement (its change 4), not traced again by me.
5. The OPEN FOR THE PILOT paragraph as a line of its own at step 11's end (before COST TABLE): STANDS.

## C. TWO LINES THE FOLD LEFT BEHIND - EXACT TEXT; NOT GATING (each anchor counted: once in the memo)
Neither changes a typed line, a test or a break: the sum and the loop are stated right elsewhere in the memo (lines 78, 331; 131). They are given
so the memo does not say two things; the coordinator folds them at the next touch or names them in T-318-2's brief. No further review round is
owed for them - each is checkable by count.
E1 (the table's heading, line 288).
- FIND: `THE 50 BREAKS (each one place; "->" = replaced by; the test that must fail). F318-01..08 and -10 are the steps' own above; the rest:`
- REPLACE BY: `THE 54 BREAKS (each one place; "->" = replaced by; the test that must fail). F318-01..08 and -10 and the review's four (-52 and -53 in step 8b, -54 in step 5, -55 in step 7) are the steps' own above; the rest:`
  (9 + 4 of the steps + the table's 41 = 54: the breaks file holds all 54, the four new ones cut from steps 8b, 5 and 7.)
E2 (step 5, line 191).
- FIND: ``the round (the `while` block above). TESTS T1, T2, T5, T6, T7, T8, T11, T12.``
- REPLACE BY: ``the round (the `for` block above). TESTS T1, T2, T5, T6, T7, T8, T11, T12, T17.``
LEFT AS HISTORY, NO EDIT: the bracket of the BREAKS SHARE line (78-79) - "the table at the end names each" (four now stand in steps) and "the
other 40 of U1's 268" (written when the share was 50). The three shares on disk are 120 + 97 + 54 = 271.

## FOR THE COORDINATOR (none is a question to the owner)
- F318's design is approved as it stands on disk (sha256 above); typing does not wait for E1 or E2.
- THE TYPED SHAPE now HOLDS changes 2, 3 and 5 in place. T-318-2's brief should say: "make section 1's lines equal THE TYPED SHAPE as it stands
  now" - a typist who looks for the review's "replace" of a line section 1 already typed in the new form finds nothing to do, and that is right.
- `whatifs/dash.py` (86-93, 404-405, one new function) is typed by step 8b: no other open row types those lines at the same time (REVIEW_F318 change 1 (d)).
- With RULINGS_U1b.md PART 3 (DRAWN-b's C11): a rejected or failed blink / mouth picture becomes a row with NO file and status "REJECTED" or
  "TRIED". F318's readers pass such a row by as far as the memo shows them (`master_tries` by hash, `his` = LOCKED with a file, `_low_master` and
  the REDOSHEETS branch = expression "master" and a DRAFT status). CR-318 and CR-DRAWN-b each check it on the tree that holds both.

## NOT READ
The memo outside the lines named above (Step 1, Step 2, steps 1 to 4 and 6, the break table's rows but 26 and 31). No code of the repo was
opened for this file. No test was run: every "fails under" above is from reading.
