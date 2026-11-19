VERDICT: APPROVED
The blocks marked R22 ( are judged in REVIEW_R22_BLOCKS_B_OWNER.md by R19.
# ROUND 3 (R18, the same reviewer; Thu 19 Nov 2026, 20:59 to 21:01 UTC, clock read) - APPROVED FOR THE MEMO WITH "R18 (1)" TO "R18 (7 g)"
JUDGED: `PREDESIGN_B_OWNER.md` as R22 left it at 20:58 UTC (1,220 lines, 144,974 bytes; the file before it is kept as
`PREDESIGN_B_OWNER.before_R22.md`, 1,038 lines, 121,877 bytes - the file of my round 2).
CHANGE 7 (g) IS IN, word for word, once (the memo's line 439; its nine lines compared with this file: none differs). R1-32
confirmed its mapping. With it, every change of rounds 1 and 2 is in the memo.
WHAT THIS APPROVAL COVERS AND WHAT IT DOES NOT, said plainly. It covers the memo as R17 left it, with my seven changes and
7 (g). It does NOT cover R22's 20 places (35 lines marked "R22 ("): by R1-32 I did not read them - R19 judges them in
`REVIEW_R22_BLOCKS_B_OWNER.md` (not yet written at 21:00 UTC). The design is approved for BUILD only when that file approves too.
TWO OF R22's PLACES TOUCH MINE, and are R19's to judge: (a) the line "- step 8: ..." of my block R18 (1) now ends "R22 (2): and
`SILENCE_LEAD_H`." - my words are whole, one cell is added in the step that reads it, as change 1 orders; (b) R22 (4), placed
after my change 5, by R22's own line makes a Short "could not be read" only after three empty reads and the hours. Checked by
search only: no line R22 removed or changed holds an "R18" mark; of my blocks only that one line moved.
USAGE (`get_usage`): the figure after this round is in my line to R1. This session takes no further reading (it stands at its
60% line); it owes one mechanical act, on R1's word: the commit of this review in the record, with R19's file appended.

# ROUND 2 (R18, the same reviewer; Thu 19 Nov 2026, 20:38 to 20:41 UTC, clock read) - ONE SENTENCE IS LEFT: 7 (g). WITH IT IN, APPROVED
JUDGED: `PREDESIGN_B_OWNER.md` as R17 left it at 20:36 UTC (1,038 lines, 121,877 bytes; the file before it is kept beside it as
`PREDESIGN_B_OWNER.before_R18.md`, 941 lines, 111,623 bytes).
ALL SEVEN CHANGES OF ROUND 1 ARE IN, WORD FOR WORD, AND NOTHING ELSE MOVED. How I checked, said plainly: a line-by-line `diff` of
the two files shows 21 places and no other - 11 lines changed, 108 added. READ BY EYE: every changed word (seven -> eight; the six
tokens `INFORM_KINDS` -> `STANDING_KINDS` and the replaced sentence; the two verbs OK -> DONE) and the nine small blocks whole
(3, 5 in PART 1, 6, 7 b to 7 f, the two ENFORCE rows) - each begins at its own "R18 (" mark with no stray words before it and ends
where mine ends. CHECKED BY A COMPARISON, not re-read: the 69 lines of the three large blocks (5 in PART 9; 4; 1 and 2 before the
table) - every line is found word for word in this file, the counts are mine (11, 22, 17 + 19), and the table's header follows
the block. One ("Done", "OK") is left on purpose (the hold's own Done of R17 ADDS (C)): right.
R1's THREE CONFIRMATIONS (R1-30) are taken: 4 (a), 5 (ii), 7 (f) stand as written.
R1's CHECK ON 7 (f) - "is anything the older Spend section showed him no longer reachable from the Money group?" YES, SOMETHING
IS LOST as the memo stands, and not only there. `send_section("money")` shows `OV.render("money", view)` - his money against the
cap and the three largest providers (`owner_view.py` 216-222) - and sends the money chart first (`wa.py` 62-63). The memo's
`send_group(g)` is only "the group's text": typed as the group's rows, that line and that chart are gone from WhatsApp. The same
holds for the seven other older sections: with the switch on no button leads to them. So ONE SENTENCE MORE, change 7 (g) below
(the last entry of change 7), with its place and exact words. It carries one small choice, said for R1: which older section
opens which group - the mapping PART 6 already gives the dashboard's tabs and item 150's own list of the eight groups.
WHEN "R18 (7 g)" IS IN THE MEMO (one search), the first line of this file becomes `VERDICT: APPROVED` - AND NOT BEFORE THE BLOCKS
MARKED "R22 (" ARE READ (WITHDRAWN AS TO ME BY R1-32: R19 judges them - see ROUND 3 above. R1-31, 20:4x UTC: V4b's reviewer measured that GitHub starts this repository's half-hourly tick about
3.5 times a day, median gap 408 minutes; a fresh designer of record, R22, writes the smallest change into the memo by about
21:20 UTC). SAID PLAINLY: nothing in my two rounds judged the tick's real cadence - I read the code and the memo, and both say
"every 30 minutes". THE MEMO's SENTENCES THAT LEAN ON A HALF-HOURLY TICK, for R22 and whoever reviews its blocks: PART 7, the
review card that expires one and a half hours before the slot and `contract.approve`'s 30 minutes (`contract.py` 1081), with
`floor.eye_hours`' "two ticks" (`floor.py` 401-405); PART 9, "the Short goes public at the next half-hourly tick, at most 60
minutes after its upload", `HD_SHORT_CAP_MIN`, `long_step`'s worked table ("ticks at :07 and :37") and `HD_GUARD_MIN` 45 ("ticks
are 30 minutes apart"), HIS WINDOW's 08:30; PART 3, `alarm_retry` "at every tick"; PART 4, the 09:00 and 18:00 pushes ("at or
after the hour": a late tick sends them late, and `needs` could go out near midnight) and `expire_defaults`; my own change 5
("the next tick asks again"). The first push of an alarm does NOT lean on it: it is sent inside the job that raised it.
USAGE (`get_usage`): 20:36 UTC context 57%, weekly Fable 44%, all models 24%; the figure after this round is in my line to R1.

# REVIEW_OF_RECORD_B_OWNER - the review of record of B-OWNER's design (with B-HDGATE), round 1, ONE COMPLETE ROUND
Pool role R18, session `local_24f616a8-b422-4422-a940-5967d753f3fb` (Fable 5.2, Extra high), Thu 19 Nov 2026, 20:07 UTC (first
clock read) to 20:29 UTC (clock read before this file was written).
I wrote nothing of the memo and rewrite nothing in it. I ran `proving/next.py` once (STATE: DRAWN, PROVING, final code commit d64fdcc,
red rounds 0 - its card is DRAWN's prover's, not mine), `date -u`, and read-only searches. No test, rehearsal, sweep or break; nothing
committed; nothing in the repository touched. Code read in the checkout at HEAD 5ca8c99 (= d64fdcc and two text commits).
THE MEMO JUDGED: `PREDESIGN_B_OWNER.md` as it stands since 20:05:13 UTC (941 lines, 111,623 bytes), WITH R7's one sentence already in
it (PART 1, "`ypp_tier` IS TOLD ONCE", the file's lines 228-233): I judged it as part of the memo. Places below are a PART and a
string to search; line numbers are of that 941-line file.
THE READING I DID (the reviewer's reading, A10, as my brief and R1-25 (4) named it):
- the memo WHOLE, line by line, every line marked "R17" against the code under it; `PREREVIEW_B_OWNER.md` whole (both rounds);
- the plan: AMENDMENTS 1 AND 2 (lines 14-72), amendment 3's lanes (73-102), A10, A12, A13 (133-150, 204-265), chapter 2, 5.3 to
  5.6; `reviews/V2b_design.md` 337-363 (the seven attacks); `RESET_BATTLE_PLAN.md` whole; the briefs' head and my section;
- `RULINGS_BY_R1.md` R1-5, R1-6, R1-11, R1-16, R1-20 (to its point 3), R1-25, R1-26;
- in `02`: items 149 and 150 whole, 151 to its TOLD lines, 156 to point 4 of its BINDS, 180 whole;
- CODE, WHOLE: `notify.py`, `wa.py`, `digests.py`, `org/desk.py`, `launch.py`, `ypp.py`, and `release.py` 1-507 - the lines 1-214
  and 310-454 that neither designer had read are read;
- CODE, IN PART: `publish.py` 40-299; `contract.py` 940-1093; `org/floor.py` 398-477; `specials.py` 364-478; `governor.py` 96-207;
  `org/palace.py` 14-43, 216-264, 420-501; `dash.py` 1-75, 128-264; `manage.py` 60-158, 176-387, 462-479, 1258-1274; `episode.py`
  90-101, 936-969; `org/runner.py` 508-525; `costguard.py` 244-265; `preview.py` 8-21, 82-137; `sheets.py` 44-123, 176-187;
  `voice_lab.py` 12-34; `breakout.py` 174-182; `truth.py` 200-211, 272-278, 301-321; all 50 `NT.send(` calls with the two lines
  after each; every import of `notify` and of `wa`; every caller of `yt_upload`, `yt_set_privacy`, `yt_schedule`;
- OLDER TESTS: `conftest.py` 1-70; `test_v94a.py` 121-166; `test_v94b.py` 30-124; `test_v12_strategy.py` 334-385, 458-467;
  `test_v12_b0b.py` 226-275; `test_v91_matrix.py` 82-97.
NOT READ, SAID PLAINLY: `02` beyond those items (of 138, 145, 146, 158, 169, 186, 187 only the headings); the plan beyond the parts
named; `LAUNCH_MAX_16NOV.md`, `FOR_FABLE_AT_THE_RESET.md`, `RELAY_OUTBOX.md`, `PLACES_B_OWNER.md`, `BUILD_STATE.md`, `00`, `01`, `03`,
`04`, `06`, the redesign, `docs/CURRENT/`; `REAUDIT_R2.md` (STEP 0b is R2's text, placed by R1-11: not judged here). Code not read:
the page `mission_control.html` (only its render functions, tabs and their lines, by search), `worker.js`, `render_check.mjs`,
`owner_view.py`, `preflight.py`, `fakes.py`, `hooks.py`, `tools/sweep.py`, `tools/rehearsal.py`, `herostill.py`, `pilots.py`,
`spinoff.py` (line 140 by search), `models.py` (the two route lines by search), `org/strategy.py` (lines 10-16 and `briefed`),
`org/levers.py` (line 21, `owner_of`), and the mail sites of `community.py`, `insights.py`, `packaging.py`, `premise.py` - those
rows of PART 2's table stand on R7's place-check. The code graph was not run (a python process; DRAWN's block is alive).
USAGE (`get_usage`): 20:07 UTC weekly Fable 35%, all models 18%, my context 11%; 20:25 UTC Fable 41%, all models 21%, context 46%.

## THE VERDICT IN SIX LINES
The design is right and should be built. R7's fourteen changes and its round-2 sentence are ALL in the memo, in the sense R7's
words require - read line by line, each against its code (the list is below). It is refused for SEVEN exact changes, each found by
opening a file or an older test that no earlier reader of this memo had opened. Three would stop the build: as ordered, the steps
are red from step 1 on (1, 2), and one older test pins a tuple the memo grows (3). Three would reach him or a viewer: a Short that
waits for HD is filed as FLAWED and never finished, or is left private when the gate is switched off (4); a made-for-kids or
unlabelled Short goes public when YouTube's answer could not be read, and a blocked Short is never told to him (5); his click
window never reaches the 18:00 list (6). The seventh is six small sentences a typist cannot guess. NO SCOPE GREW in the memo.

## THE CHANGES (each is "the memo must ..."; the place and the exact words are given - nothing is left to judgment)
HOW THEY GO IN (for a script): an INSERT names the exact words it follows (or the line it stands before) and is its own paragraph;
a REPLACE names the exact words it replaces. In change 3 do (i) before (ii).

1. THE ORDER OF THE BUILD - NOTHING MAY BE TYPED AHEAD OF ITS USER. `tests/test_v12_b0b.py` 233-242 fails on any Settings cell that
   no code names (`truth.unread_settings` must equal `truth.UNREAD_SETTINGS`, a list that may only shrink, `truth.py` 201-211,
   272-278); lines 250-259 do the same for a Sheet tab and a function (`UNUSED_TABS`, `UNWIRED_FUNCTIONS`, 301-315). The table's
   step 1 holds "the cells ..., the appended columns and tabs" and `notify.mail`: fifteen cells and the tab `HD_Wait` would stand
   unread until steps 4 to 10 - a red Checks run at step 1 and at every step after it (R1-6: a red run is a red).
   INSERT, standing BEFORE the line `| Step | What | Files | Tests |`:
   "R18 (1): NOTHING IS TYPED AHEAD OF ITS USER - WHERE THIS BLOCK AND THE TABLE BELOW DIFFER, THIS BLOCK IS THE ORDER. Two older
   meta-tests are red on anything added before code uses it: `tests/test_v12_b0b.py` 233-242 (a Settings cell that no code names
   must stand in `truth.UNREAD_SETTINGS`, a list that may only shrink) and 250-259 (the same for a Sheet tab and a function:
   `UNUSED_TABS`, `UNWIRED_FUNCTIONS`). So each cell, tab and column enters with a `core.py` line IN THE STEP THAT FIRST READS IT:
   - step 1: `TWO_SCREENS_ON`; the three columns of `Owner_Actions`; in `tests/conftest.py` `OLD_SCREENS = {"TWO_SCREENS_ON":
     "FALSE"}`. `notify.mail` is NOT typed in step 1.
   - step 2a: `notify.mail`, with its first callers (`notify.py` joins the step).
   - step 4: `NEEDS_HOUR_IST`, `NEEDS_SENT` (an "auto" cell, as `DIGEST_DAILY_SENT`), `WA_OPEN_TEMPLATE`, `PRICE_WA_UTILITY_INR`,
     `PRICE_WA_SERVICE_INR`, `WA_SERVICE_FREE_PER_MONTH`, `WA_MONTHLY_CAP_INR`.
   - step 5: `DESK_MONTHLY_CAP_INR`; the three columns of `Owner_Desk`.
   - step 8: `CREATIVE_REVIEW_WAIT_H`; the column `checks` of `Specials`.
   - step 9a: `HD_GATE_ON`, `HD_SHORT_WAIT_S`, `HD_SHORT_CAP_MIN`; the tab `HD_Wait`; the entry `"HD_GATE_ON": "FALSE"` of
     `OLD_SCREENS` (the file's own rule, `tests/conftest.py` 16-17: an entry is added in the step that adds its cell).
   - step 10: `HD_LONG_LEAD_MIN`, `HD_STEP_MIN`, `HD_GUARD_MIN`, `HD_LONG_CAP_MIN`; the three columns of `Episodes`.
   In each of those steps `tools/gen_docs.py` is run and `docs/CURRENT/SYSTEM.md` is committed with the step
   (`tests/test_docs_current.py` 60-72), not only in step 11. Appended columns pass the golden schema - `tests/test_v91_matrix.py`
   89-92 compares a prefix - so the read that the last part's point 2 left to the typist of step 1 is done."

2. THE ORDER OF THE BUILD - STEP 3 CANNOT BE GREEN BEFORE STEP 4, AND FIVE TEST CLAUSES READ A LATER STEP'S FILE. Five of step 3's
   six tests read a push (`WA.push("alarm", row)`, a WA_Outbox row, `_post`), and `wa.push` is step 4's; the planted alarm test
   also reads `build_snapshot()["alarms"]` (step 6); `test_needs_you_is_one_list` (step 1) reads `digests.head` (step 4) and
   `dash._docket` (step 6); step 6's `UNPOST` calls `contract.unpost` (step 8); `hdgate.tick` is "called in `manage.tick`" and
   `manage.py` is in no step before 10.
   INSERT, right after the block of change 1 (still before the table):
   "R18 (2): THE TYPING ORDER IS 0, 0b, 1, 2a, 2b, 4, 3, 5, 6, 7, 8, 9a, 9b, 10, 11 - STEP 4 IS TYPED BEFORE STEP 3; the numbers
   stay. Five of step 3's six tests read a push (`WA.push("alarm", row)` and its WA_Outbox row), and `wa.push` is step 4's; step 4
   needs nothing of step 3 but `notify.alarm_retry` in the paused branch. So THE PAUSED BRANCH (`manage.py`;
   `test_a_pause_does_not_silence_him` and its break) moves from step 4 to step 3, and step 4 does not touch `manage.py`. Step 3
   then finds `NEEDS_HOUR_IST` and `WA_MONTHLY_CAP_INR` in `core.DEFAULTS` when it names them in `OWNER_ONLY`.
   A TEST CLAUSE IS TYPED IN THE STEP THAT HOLDS THE FILE IT READS - typed earlier it is red at its own commit (R1-6):
   - `test_needs_you_is_one_list`: step 1 proves `needs()` and `notify.digest`; step 4 adds `digests._risks`, `digests.head` and
     `wa.push("needs")`; step 6 adds `dash._docket`.
   - `test_an_alarm_arrives_on_both_screens_whatever_is_set`: step 3 proves the WA_Outbox row and the one mail; step 6 adds the
     row in `build_snapshot()["alarms"]`.
   - `test_week_and_fyi_reach_both_screens`: step 4 proves the morning message's groups; step 6 adds the snapshot's `groups`.
   - THE VERB `UNPOST|<ep>` of `dash.route` is typed in step 8, with `contract.unpost` (`dash.py` joins step 8 for that one
     branch); step 6 types INPUT only. `test_undo_is_private_never_gone` taps the verb through `dash.route`.
   - THE READ-BACK of `test_undo_is_private_never_gone` is real only from step 9a (until then the stand-in keeps no privacy and
     a long video reads private from its own upload): step 9a adds to that test "the stand-in first shows the video public, then
     `unpost`, then private".
   - THE CALL of `hdgate.tick` in `manage.tick` (after `release.settle`, in a try of its own, as its neighbours) is typed in
     step 10, with a test that runs the real `manage.tick` and sees a WAITING row finished. Until then step 9a's tests call
     `hdgate.tick` themselves, and a waiting Short is finished by `release.settle`'s pass through `_youtube`."

3. PART 1 - `INFORM_KINDS` IS PINNED, AND THE OLDER PATH READS IT. The memo grows the literal to four kinds.
   `tests/test_v12_strategy.py` 467 asserts `NTF.INFORM_KINDS == ("strategy", "desk")` - the last clause of the very test whose
   line 464 the memo says "passes with the eight and is not changed". The literal is read with the switch OFF by `notify.digest`
   (166), `digests._risks` (18) and `dash._docket` / `dash._decided` (20, 62): grown, an `idea` card leaves the older lists, and
   `tests/test_v94a.py` 164-165 (an `idea` row must show under "Waiting for you") goes red too. Two reds at step 1.
   (i) REPLACE the token `INFORM_KINDS` by `STANDING_KINDS` everywhere in the memo (seven hits: lines 196, 237, 239, 472, 492,
   560, 565).
   (ii) THEN REPLACE the sentence that begins "`STANDING_KINDS` stays a literal and grows to" and ends "never expiring." (it runs
   over lines 196-197) by:
   "`INFORM_KINDS` is NOT changed: it stays `("strategy", "desk")`. R18 (3): `tests/test_v12_strategy.py` 467 asserts that tuple
   exactly, and with the switch off `notify.digest` (line 166), `digests._risks` (18) and `dash._docket` / `dash._decided` (20,
   62) read it - grown, it would take an `idea` card out of the older lists (`tests/test_v94a.py` 164-165). The new literal
   beside it is `STANDING_KINDS = INFORM_KINDS + ("idea", "decided_post")`: rows that tell him what was done, with an undo or a
   next step, never counted as waiting, never given an expiry by the inform rule. Code behind the switch reads `STANDING_KINDS`;
   the older path reads `INFORM_KINDS`, word for word as today."

4. PART 9 - THE SHORT'S `privacy` RECEIPT DOES NOT FIT `release.py`, `finish` IS DEFINED NOWHERE, AND THE KILL SWITCH STRANDS A
   SHORT. Read: `want_youtube` (153-158) builds its body with `yt_body`'s default, so `want["privacy"]` and the body it returns
   say "public"; `compare` runs at EVERY pass (264) and writes `privacy` DRIFT for a Short that waits; `state_of` (182-185) then
   says FLAWED, a FINAL state - `short()` (445) judges the sheet at once and `settle` (495, 505) never runs the door again; line
   262 keeps on record a body that was not sent. The memo says the row "is WAITING while it waits" and never says who writes it;
   `hdgate.finish` is named twice and defined nowhere. And with `HD_GATE_ON` turned FALSE while a Short waits, `_youtube`'s older
   path would read "asked public, came back private" as THE LOCK (265): a false alarm, `UPLOAD_LOCK` on, production paused.
   INSERT after the words `then public: set by us and read back".`:
   "R18 (4): WHO WRITES THE `privacy` RECEIPT, AND WHAT `finish` IS (read whole: `release.py` 1-507).
   (a) A VIDEO IS GATED WHEN IT HAS A ROW ON `HD_Wait` (`hdgate.row(vid)`; `enter` writes one only when the upload went through
   the gate) - never by what the switch says at a later pass. `HD_GATE_ON` FALSE lets nothing NEW in; `hdgate.tick` and `finish`
   still finish every row that waits, and `_youtube` still treats a gated video as gated: a Short the gate took private is never
   left private, and never read as "the lock", because the switch was turned. (The long video's gate simply stops moving times:
   YouTube's own schedule publishes it.)
   (b) IN `_youtube`, FOR A GATED VIDEO: the body kept on record says private (`body["status"]["privacyStatus"] = "private"`
   before `_save(..., sent=body)`: what was really sent); `privacy` is taken out of `want` before `compare`, which never judges
   that row; line 265's lock call is skipped; and after `_extras_youtube` the row is written from the gate alone - `state, m,
   note = HG.finish(vid, wait_s, now)`: WAITING -> [WAITING, "private until YouTube shows it in HD: m min so far"]; PUBLIC ->
   [KEPT, "public after m min; HD yes"]; CAP -> [KEPT, "public after m min; HD NO (the cap)"]; BLOCKED or LOCKED -> [DRIFT, note].
   (c) `hdgate.finish(vid, wait_s, now) -> (state, minutes, note)`: the video's `HD_Wait` row; a row that no longer waits is
   answered as it stands; else `yt_read` is asked every `release.POLL_S` seconds until `short_step` says public or cap or
   `wait_s` is used up; on public or cap `go_public`; then the row's state. `hdgate.tick` is the same call with `wait_s` 0 for
   every WAITING row.
   (d) `settle` IS NOT CHANGED: a WAITING `privacy` row keeps the record OPEN through `state_of`, and the OPEN branch runs the
   door again at every tick while the thumbnail does not wait (504); when both wait, `hdgate.tick` still makes the Short public
   at its cap and the next pass writes the receipt.
   Tests: `test_a_waiting_short_is_open_not_flawed` (fault `sd`: after the first pass the record is OPEN, `privacy` is WAITING,
   the release gate has not run, `sent` says private; at the cap KEPT "HD NO (the cap)" and DONE);
   `test_the_switch_never_strands_a_short` (fault `sd`, the gate switched off while it waits: public at its cap, no lock,
   `UPLOAD_LOCK` untouched). Breaks: `privacy` left in `want`; `tick` returns when the switch is off."

5. PART 9 AND PART 1 - A READ THAT FAILED IS TAKEN AS A PASS, AND A BLOCKED VIDEO IS TOLD TO NOBODY. `publish.yt_read` answers
   `{}` when the call fails or the video is not found (199-208). `go_public` "judges its own `yt_read`": on `{}` there is no kids
   flag and no AI field, so the video goes public with NEITHER policy read made - R7's change 1 (b) undone by a network fault.
   The same `{}` in `hdgate.tick` reads as "not private", so "already public". And `block` for the AI label reaches only
   Publishing (`release._gate_emit`: a memo from D8 to D9): the Short is private for ever and neither screen says so (item 149:
   "a missed one can keep a video private"). The kids flag has its alarm; a lock has its alarm; this one has nothing.
   INSERT after the words `The release gate then judges the receipts as today.`:
   "R18 (5): A READ THAT FAILED IS NOT A PASS, AND A BLOCK IS TOLD. (i) `publish.yt_read` answers `{}` when the call fails (line
   208). On an empty read `go_public` changes nothing and returns (False, "not read"): the row stays WAITING and the next tick
   asks again; `hdgate.tick` treats an empty read of a long video the same way - it writes nothing and moves nothing (an empty
   read is not "already public"). A Short still unread `PRIVATE_ALERT_HOURS` after its cap is BLOCKED, "YouTube could not be
   read". (ii) `block` TELLS HIM, once a video: kind `hd_blocked`, text "<title or id> stays private: <why>. Nothing was
   deleted. Put it right in YouTube Studio and make it public there: https://studio.youtube.com/video/<vid>/edit", key
   `hdblock|<vid>`, tier "now", no button (so `send` gives it "Done"). Without it a Short blocked for its AI label is private
   for ever and only a memo to Publishing says so; a kids flag has its alarm and is told this way as well. Tests:
   `test_an_empty_read_makes_nothing_public` (`yt_read` replaced by `{}`: private, WAITING, no row to him; `PRIVATE_ALERT_HOURS`
   past the cap: BLOCKED and one `hd_blocked` row); `test_a_dropped_label_is_repaired_once_or_blocked` gains "one `hd_blocked`
   row under Needs you". Breaks: an empty read is taken as clean; `block` sends nothing."
   INSERT after the words `un-pause, is his own sitting and has no card.`:
   "R18 (5): HOLD (a) gains `hd_blocked` (PART 9: a video the HD gate keeps private for a policy read; group "needs"; in the
   pinned tuple with that reason)."
   INSERT after the row `| R17: A taken input can be taken back | desk._do | test_a_taken_input_can_be_taken_back |`:
   "| R18: A waiting Short is open, never flawed; the switch strands none | release._youtube, hdgate.finish | test_a_waiting_short_is_open_not_flawed; test_the_switch_never_strands_a_short |
   | R18: A read that failed is not a pass; a block is told | hdgate.go_public, hdgate.block | test_an_empty_read_makes_nothing_public |"

6. PART 9 AND PART 2 - HIS CLICK WINDOW NEVER REACHES THE 18:00 LIST. `asks(row)` counts a button only when its verb is not `OK`,
   `NOTED` or `SEEN`; `prepublic` and `pin_comment` are sent with ("Done", "OK"). So neither is in `notify.needs()`, neither is
   counted under "Needs you", and `wa.push("needs")` - which the memo's own (C) builds from `needs()` - never lists them, while
   HIS WINDOW says "later, in the 18:00 list" and item 156 binds "a late upload moves its clicks to the 18:00 list". With nothing
   else open, no 18:00 message is sent at all and the end-screen click passes unseen.
   REPLACE `card: [("Done", "OK")], default "the comment stays unpinned"` by `card: [("Done", "DONE")], default "the comment
   stays unpinned"`.
   REPLACE `Studio: <link>." with ("Done", "OK"),` by `Studio: <link>." with ("Done", "DONE"),`.
   INSERT after the words `it stays with the after-public clicks of the release card.`:
   "R18 (6): `prepublic` and `pin_comment` carry the verb DONE, not OK: `asks` counts it, so both stand under "Needs you" and in
   the 18:00 list with their deadline and their default (item 156: a late upload moves its clicks to the 18:00 list). With OK
   they were in neither list. No handler is needed: his tap closes the row. `test_his_window_card` asserts the card is a row of
   `needs()` and of the list `wa.push("needs")` sends. Break: the verb back to OK."

7. SIX SMALL SENTENCES A TYPIST CANNOT GUESS.
   (a) STEP 0b's paragraph still says seven. REPLACE `(step 3 adds seven cells to` by `(step 3 adds eight cells to`.
   (b) `enter`'s `kind` has no source: `yt_upload` knows only `short`. INSERT after the words `R17 ADDS (E): the tab's column
   `ai` keeps what the upload asked for.`: "R18 (7 b): `kind` is "short" when the upload was called with `short=True`, else
   "video"; `cap_min` is `HD_SHORT_CAP_MIN` for both."
   (c) `_await_review` runs BEFORE the Specials row is written (`specials.py` 389-392), so it has no row to read `checks` from.
   INSERT after the words `The held Short keeps `special_review` and waits for him: its file failed a check.`: "R18 (7 c):
   `_await_review` gains the parameter `checks=""` and `make` passes `rec.get("checks", "")` (nothing sets it today): the
   `special_ready` branch runs in the planted test and for the batch that records a special's check."
   (d) The lock cannot be planted with `drift`: in the stand-in's read `fixed` wins over `drift` (`publish.py` 197). INSERT
   after the words "`ready(got) = processed and hd`.": "R18 (7 d): the fake `yt_set_privacy` honours `refuse` and `ignore` for
   "privacy" exactly as `yt_set_label` does for "label" (`publish.py` 155-156); `test_a_private_read_back_is_the_lock` plants
   `ignore: ("privacy",)`."
   (e) In fake mode `ypp._query` returns no rows, so `ypp.check` never sends. INSERT after the words `own clock until the form
   is sent: that is its purpose.)`: "R18 (7 e): in `test_the_tier_is_told_once` `ypp.progress` is replaced by a dict that
   qualifies. The rule sits behind the switch, like every rule of PART 1."
   (f) `MENU|money` is today's Spend section AND the new Money group (`wa.py` 33-36, 173-177); "the group's own action" is said
   and never named. INSERT after the words "more than three buttons = a list whose rows are `ACT|<aid>|<i>`).": "R18 (7 f): WITH
   THE SWITCH ON `MENU|<x>` is the new group when `x` is one of `GROUPS` (`MENU|money` is the Money group, not the older Spend
   section), and `MENU|menu` and the typed words `menu`, `hi`, `start`, `options` send the eight-group list of the morning
   message (item 150: the menu IS the eight groups); any other `MENU|<section>` is answered as today. THE GROUP'S OWN ACTION
   exists for two groups only: needs -> ("Open the list", `OPEN|needs`); decided -> ("Undo or take down", `CARD|<aid>`) for the
   newest open row of the group that carries a button. A group without one sends two buttons."
   (g) ROUND 2, R1's check on (f): the older sections lose their button and `send_group`'s text is not said. INSERT after the
   words `A group without one sends two buttons.` (the end of 7 (f)'s paragraph in the memo; found once):
   "R18 (7 g): NOTHING THE OLDER MENU SHOWED IS LOST. With the switch on the older sections have no button of their own, so EACH
   GROUP'S TEXT OPENS WITH THE OLDER SECTIONS IT REPLACES, rendered by today's `OV.render(name, OV.build())`, and its own rows
   follow: posted -> `today`, `numbers`; learned -> `experiments` and `digests.learned()`; research -> `hot_topics`,
   `observations`; plan -> `strategy`, `recommendations`; money -> `money` (his money against the cap and the three largest
   providers); needs, inputs, decided -> their rows only. The two charts go with them as `send_section` sends them today
   (`wa.py` 62-63): the numbers chart before the posted group, the money chart before the money group. Where the text passes
   1,024 characters it is cut at a line and ends "more on the dashboard". Test `test_the_groups_carry_the_older_sections`: with
   the switch on, the text `send_group` sends for money holds the first line of `OV.render("money", view)` and an image went
   before it; the same for posted and `numbers`. Break: the money group sends its rows only."

## THE TEN QUESTIONS OF 5.4
1. Serves him or a viewer, in a layman's words? YES - parts 1 to 8 the operator of the launch, part 9 every first viewer.
2. Every word of the owner? NO on two: item 149 (a Short the gate blocks is kept private and he is never told - change 5) and
   item 156 (his clicks do not reach the 18:00 list - change 6). Items 150, 151, 180 are honoured as R7 left them.
3. Enforceable as written? NO - changes 1, 2 (the steps are not green in their order), 3 (a pin), 4 (a receipt nobody writes).
4. Taste by a cheap model, a model's opinion as a gate? NO - `owner_desk` is the Board's chain (`models.py` 154, 530); code decides.
5. Judged on what really happened, both kinds of cases? YES, with change 5: a read that failed must not count as a clean read.
6. Money? YES - WhatsApp's rows match no prefix of `governor.py` 143 or 146 (read `month_spend_of`, 104-113): they are his own
   spend. Said plainly: the chat's cap stays soft, as today (above Rs 250 the chat goes on with its cheap model).
7. Reuse? YES - `notify`, `wa`, `digests`, the release sheet's WAITING state, `floor.eye_sweep`'s pattern.
8. Older pins, each named? NO - `INFORM_KINDS` (change 3) and the two ratchets of `test_v12_b0b.py` (change 1).
9. The worst this design could still let through: before change 5, a made-for-kids Short made public on a failed read. After
   the changes: a film approved by his silence that he would have held - the floor, the slop guard, the contract, his Hold
   before it and "Take it down" after it stand.
10. What only reality can answer is written down? YES (FOR THE PILOT); nothing to add.

## R7's FOURTEEN CHANGES AND ITS ONE SENTENCE - EACH IN, READ AGAINST THE CODE
1 (the gate never public before its checks): IN - `go_public` holds both reads, `finish` is `_youtube`'s last act (`release.py`
  257-269 read); completed by changes 4 and 5. 2 (the stand-in merges): IN, right against `_fake_put` 64-72 and line 197.
3 (a, b, c): IN - `launch.py` 50-51 asks unlisted; `spinoff.py` 140 is the only `privacy="public"`; a time is set in three
  places (`episode.py` 864, `contract.py` 1084, `manage.py` 83), counted by my own search. 4 (the inform row closes): IN, right
  against `notify.py` 69-71 and 135-150. 5 (a, b, c): IN. I attacked the "Seen" button for R7's own round-2 hole and it holds:
  every alarm site has its own once-guard (`manage.py` 312 a month, 345 a video, 1269 three days; `episode.py` 98 a day;
  `launch.py` 83-84 a day; `runner.py` 517 once a day; `manage.py` 563 stops at True). 6: IN - eight cells; the pin's expression.
7 (a to d): IN, right against `contract.py` 971-993, 1002-1013, 1072-1093 and `floor.py` 447-459. 8: IN - I counted 50 calls,
  48 literal, 44 kinds (R17's count; R7's "46" was a miscount), every one in the register, and every module imports notify as
  `NT`, so the scan sees them all. 9 (a, b, c): IN. 10 (a to e): IN - every field of the Palace item passes `palace.check`
  216-264; `START` and `MOVES` give the owner both moves. 11 (a to d): IN - `STR.briefed` does stamp the desk (`strategy.py`
  478). 12: IN. 13: IN, completed by changes 1 and 2. 14 (a to f): IN - rows 32, 34, 35, 38 read against `preview.py` 131
  (`DRAFT\d{8,14}`: the verb reaches `preview.decide`), `sheets.py` 63, 98, 103-114 and `voice_lab.py` 24-32.
THE CARD SCAN's four cards are the whole list: I read every `NT.send(` call of a CARD kind; `style_pick` (`sheets.py` 183) and `breakout`
(`breakout.py` 181) carry both words. R17's SIX ADDED SENTENCES: (A), (B), (D), (E), (F) right; (C) right with change 6.
R7's ONE SENTENCE (`ypp_tier` is told once): RIGHT and typeable against `notify.py` 69-71 and `ypp.py` 31-36; with 7 (e).

## THE SEVEN ATTACKS
(a) Exact enough to type? Not as written: 1, 2, 4, 7.
(b) False about today's code: "`INFORM_KINDS` ... grows" against its pin; "`tests/test_v12_strategy.py` ... is not changed"
    (true only with change 3); "the row `privacy` is WAITING while it waits" (`compare` writes it first); "`release.settle`
    treats a WAITING `privacy` row as it treats a WAITING thumbnail" (it reads only the thumbnail's receipt, 503 - the sentence
    holds through `state_of`, said in 4 (d)); "step 3 adds seven cells"; "later, in the 18:00 list". TRUE as checked: every
    line R7 marked true, and the places listed under the fourteen.
(c) A good thing held for a reason the rule does not know: a waiting Short filed FLAWED (4). A bad one passed: a failed read (5).
(d) Every reader of an open row: `notify.digest` 166, `digests._risks` 18, `dash._docket` 20, `dash._decided` 62, the chat's
    `open_items` (`wa.py` 118) and the status line (192) - all five of (C) and the two of `dash`; with change 3 none moves
    with the switch off.
(e) The order: changes 1 and 2. With them every step is green alone: 0, 0b, 1, 2a, 2b, 4, 3, 5, 6, 7, 8, 9a, 9b, 10, 11.
(f) What he gets, in his words: as R7 wrote it; and with these changes - a Short that waits for HD is finished, never dropped;
    nothing goes public on a read that failed; a video the gate keeps private is on both his screens with what to do; his
    end-screen and pin clicks are in the 18:00 list.
(g) The worst case: question 9.

## EACH STEP, ONE TYPIST (item 186) - AFTER THE CHANGES
Still 15 steps, no step added. Step 4 is lighter (no `manage.py`, which A9 (5) makes a typist read whole); step 3 takes the
paused branch; step 2a takes `notify.mail`; step 8 takes one branch of `dash.py`; steps 4, 5, 9a, 10 each take their own lines
of `core.py`.
THE TYPIST OF STEP 9a READS `whatifs/release.py` WHOLE BEFORE TYPING - YES (R1's question; 507 lines, 38 KB, about 15,000
tokens: it fits the step). The Short's door cannot be typed from lines 257-270 alone. Change 4 leans on `want_youtube` (153-158),
`compare` (160-180), `state_of` (182-185), `_extras_youtube` (234-255), `_one` (347-364: where the state is computed and saved),
`_release` (367-393: the status "POSTED" and `ladder.went_public`), `short` (438-446: when the release gate runs), `report`
(448-470: a WAITING row or a missing `privacy` receipt fails check `release_sheet`) and `settle` (481-507). A typist who reads
only `_youtube` writes a receipt that `compare` overwrites at the next pass.
NO SCOPE GREW in the memo. Said plainly of my own changes: change 5 adds one message kind (`hd_blocked`), the voice
of a hold the memo itself creates; nothing else adds a part.

## OBSERVATIONS - NO CHANGE REQUIRED (for the builder's open issues and the finisher)
- A STALE HOLD ROW CAN MAKE HIS SILENCE WAIT. `clear_to_post` (2) counts any open HOLD row of the episode. The contract card's
  "Approve anyway" waives `viewer_floor` and leaves the `floor_hold` row open for ever (it never expires, `floor.py` 417-418);
  the mail's fix link (`episode._fix_link`) leaves `contract|<ep>|final` open up to 48 hours. Then a film that passed is not
  approved by silence; he gets the `silence|` row and one tap. Open issue with its fix: (2) ignores a HOLD row older than the
  episode's newest clean final-gate rows.
- "DISCUSS" ON THE REVIEW CARD ANSWERS THE ROW (`contract._answer` 1013): the card is ANSWERED, never DEFAULTED, so
  `review_sweep` never approves and the film waits with no card. Today's behaviour, kept: an open issue (item 150).
- A BLOCKED SHORT READS "POSTED" on tab Specials and its ladder clock runs (`release.py` 391-392). Add to 14 (b)'s open issue.
- `desk.take` WITH `STRATEGY_ON` FALSE is not said; the reading that loses nothing: his words are stored, the weighing follows
  `desk.on()` and `EX.on()` as `tick` does today (lines 65, 72-73).
- `org/seed/owner.json` holds `owner_preference` examples (its line 2); the memo needs none - its fields pass the gate.
- In the real mode `verify_upload` (`publish.py` 139-145) already sends the kids alarm at upload; `go_public` sends it again
  under the same key: one incident, count 2. Right.

## WHAT IS SOUND AND SHOULD NOT MOVE
Everything R7 named; and by my own eye: the register (complete at d64fdcc); the alarm as an incident with a retry until
WhatsApp takes it; `clear_to_post` as a second look through the gate's own expression; the `silence|` row that reports and never
deadlocks; the stand-in that merges; `public_at` with one writer; the gate that leaves a public video alone; `long_step`'s
arithmetic (I recomputed the worked table and the 14:44 row); the Palace item, field by field; the money inside the chat's cap.

## FOR R1
- EVERY CHANGE HAS ITS EXACT WORDS; none needs a designer. THREE SENTENCES CARRY A SMALL CHOICE, each made the smallest way; if
  you want a designer's eye anywhere, it is there: 4 (a) (the switch never strands a waiting Short), 5 (ii) (one kind,
  `hd_blocked`), 7 (f) (the group's own action on WhatsApp).
- TYPING AHEAD: a step 1 already typed from the table must drop the cells and the tab it does not read, and `notify.mail`
  (change 1), and must keep `INFORM_KINDS` as it is (change 3). Steps 3 and 4 swap (change 2).
- THE WAY TO THE RECORD: the words go into the memo in this notes folder first (A13 (a)); I read the changed lines there - the
  search "R18 (" and each block against this file - and then this review's first line becomes `VERDICT: APPROVED` with a
  round-2 note, so the record gets the corrected memo and one approving review. Until your word I touch nothing in the
  repository and run nothing.
- WHERE THIS SESSION STANDS (20:36 UTC, `get_usage`): context 57% MEASURED, after the section FOR V4b; weekly Fable 44%, all
  models 24%. It has room for exactly TWO more things: the reading of the changed lines after the insert (my own words, read
  back in the memo: about 1% of the window) and the commit of this review in the record. It takes NO other question: anything
  more that needs judgment on B-OWNER belongs to a fresh Fable session with the memo, R7's review and this file.

## FOR V4b (R1's three questions on the section "FOR B-OWNER's DESIGNER OF RECORD" of `PREDESIGN_V4b.md`, read as it stands at
## its lines 1333-1352, 20:35 UTC; R1-27 (4): none of its lines needs B-OWNER's memo changed - CONFIRMED, no change of mine comes from it)
(1) LINES 1 AND 2 - DOES B-OWNER's MEMO FORBID THEM OR SAY THE OPPOSITE? NO, for both.
- Line 2 (the long loop passes over a video that is done): B-OWNER says the same thing by another key - PART 9, "R17 ADDS (A)":
  `hdgate.tick` reads `yt_read` first and leaves alone a long video whose `privacy` is not "private". A video V4b made public
  through `go_public` reads public (the stand-in records it: PART 9, R17 (2)), so it is never pushed, pulled or scheduled again.
  My change 5 (i) keeps that true on a failed read (an empty read moves nothing). `test_a_public_video_is_never_scheduled_again`
  holds with V4b's line and without it. V4b types nothing in `hdgate.py` for line 2.
- Line 1 (`go_public` on a video with NO `HD_Wait` row): nothing forbids it, and NOTHING DEFINES IT. Two sentences of B-OWNER
  presume a row: "writes the minutes and the HD state on the video's `HD_Wait` row" (WHAT V4b LEANS ON, second point) and "`ai`
  is False on a row whose `ai` is TRUE" (PART 9, R17 (1 b)). A long video never has a row - it is uploaded with `publish_at`,
  so `enter` is never called. B-OWNER itself never calls `go_public` without a row (`finish` and `tick` start from rows), so
  the built code may do nothing for such a video. SO V4b TAKES DQ 9's SECOND READING AS ITS PLAN, NOT AS A MAYBE: act a calls
  `hdgate.enter(vid, "long", now)` and then `hdgate.go_public(vid, now, why)`. That works against B-OWNER as designed: `enter`
  takes any `kind` and `ai` is a keyword with a default; with no `ai` on the row the label repair does not fire and the kids
  read still does. Three things V4b must then know: (a) `go_public` can answer (False, "blocked: ...") or, with my change 5,
  (False, "not read") - a row left WAITING is finished by `hdgate.tick` at a later tick like any other row; (b) `go_public`
  does not write the Episodes row: `public_at` and `hd_gate` for an early release are V4b's own two cells to write in its own
  commit - no B-OWNER test scans for other writers of `public_at` (R17 (3 c) is a sentence and one test about a pause, not a
  scan); (c) `test_every_public_upload_passes_the_gate` passes, because V4b calls `go_public` and never `yt_set_privacy`.
- ONE ROAD V4b MUST CURE IN ITS OWN COMMITS, said because it is today's code and B-OWNER does not touch it: `manage.hold_scheduled`
  (60-68) takes private EVERY row whose status is SCHEDULED with a slot still ahead - it does not read YouTube. A Part 2 that
  V4b released early and left SCHEDULED would be taken private by the next pause, and `resume_held` (83) would then ask
  `yt_schedule` for a video that has been public: YouTube refuses, line 86 catches it, the video stays HELD and private. An
  early release must leave the row in a status `hold_scheduled` passes over. (The same road exists today for a video he makes
  public by hand in Studio before its slot: an open issue for B-OWNER's builder, no change.)
(2) LINE 3 - AFTER `unpost`, CAN ANY ROAD OF B-OWNER GIVE A TIME TO A VIDEO THAT HAS BEEN PUBLIC? NO. NOT A REQUIRED CHANGE.
  The memo rules it out in PART 7, "R17 ADDS (B)": "No card offers Approve after a take-down: YouTube gives a time only to a
  video that was never published (S5), so `contract.approve`'s `yt_schedule` would be refused on a film that had been public",
  and again in "WHAT MOVED UNDER YOU" (3). Checked in the code, road by road: `unpost` leaves status HELD_BY_OWNER, which only
  `contract.hold_review` writes (1089) and no code moves on (the two other mentions are lists: `digests.py` 15, `episode.py`
  608); `contract.approve` has two callers - `_answer` (1012) and `floor._approve_eye` (452); `_answer` is reached only through
  `notify.answer`, which refuses a row that is not OPEN (122), and every card that carries `APPROVE <ep>` is closed before the
  video can be public (the review card is DEFAULTED or ANSWERED; `approve_by_silence` closes the `silence|` row before it
  approves; the `decided_post` row is ANSWERED by the take-down itself); `_approve_eye`, `review_sweep` and `eye_sweep` act on
  AWAITING_APPROVAL only; `resume_held` on HELD only (73); `long_step` on SCHEDULED only. So V4b's stand-in that refuses a
  `publish_at` for a record that ever read public breaks no B-OWNER test, and "Bring it back" through `go_public` with one
  branch at the head of `approve` is V4b's own, as R15 wrote.
(3) LINE 4 - (a) A HOLD ROW WITH AN EXPIRY AND A DEFAULT (`org_lever`, 72 hours, "it stays as it is"): NOT FORBIDDEN. The card
  rule (PART 7) DEMANDS both of a CARD and EXEMPTS a HOLD; it bans neither. Two HOLD kinds carry both today (`contract_hold`
  48 hours "stays held", `contract.py` 999-1000; `special_review` 72 hours "not posted"). `test_the_lists_are_pinned` pins the
  kinds, not their hours. What follows from it: at the expiry `expire_defaults` closes the row as DEFAULTED and it leaves "Needs
  you"; nothing else runs unless V4b registers `on_default` for `org_lever` (`notify.py` 143-148).
  (b) THE INFORM KIND "appetite": NOT FORBIDDEN in `KINDS` (only `ALARM_KINDS` and `HOLD_KINDS` are pinned). BUT NOT INTO
  `INFORM_KINDS`: by my change 3 that literal stays `("strategy", "desk")` - `tests/test_v12_strategy.py` 467 pins it and
  NEITHER batch changes that test. "appetite" joins `STANDING_KINDS`, the new literal. TWO EXACT WORDS FOR V4b's MEMO (R19 or
  its paster): in its line 4 of this section replace "and `INFORM_KINDS` in V4b's build" by "and `STANDING_KINDS` in V4b's
  build"; and in its list of tests changed by design delete "`tests/test_v12_strategy.py` 467 (`INFORM_KINDS` gains "appetite"
  after B-OWNER's four);". A row of a kind in `STANDING_KINDS` gets no expiry from the inform rule: V4b's caller passes its
  own (as `decided_post` passes 168 hours), or the list on Home grows without end.
VERDICT: APPROVED
# REVIEW_R22_BLOCKS_B_OWNER - the review of the blocks marked "R22 (" in `PREDESIGN_B_OWNER.md` (the tick's real cadence; R1-31 (4))
THE REVIEWER: pool session R19 `local_2bd81c62-9bcc-4c0f-96e7-6e1003ab0725` (Fable 5.2, effort xhigh), which measured the tick first and
wrote none of these blocks. Asked by R1 (R1-31 (4)); R18 stands at its line and reads no more. 19 Nov 2026, 20:57 to 21:04 UTC (clock read).
REVIEWED: the memo as it stands at 144,974 bytes / 1,220 lines - every line that carries "R22 (" (40 marks on 35 lines): R22 (0) lines 3-47, (1)
196-198, (6) 476-483, (2) 684-730, (4) 861-870, (5) 875-877 and 951-966, (3) 900-926, 975, 1042, (7) 1068-1073, (8) 1137-1148, 1175,
1212. NOTHING ELSE of the memo was read again (its parts 7 and 9 I had read at 20:35 for V4b). THE CODE THEY LEAN ON, read: `contract.py`
1052-1093 (`review_needed`, `await_approval`, `approve`), `org/floor.py` 399-405 (`eye_hours`), `manage.py` 59-86 and 176-284 (`tick`,
`hold_scheduled`, `resume_held`), `mission_control/worker.js` 106-133, `pipeline.yml` 1-63. NOT READ: `tests/test_v12_floor.py` 675-678
(the pin R22 names: taken on its word), `release.py`, `notify.py`'s `expire_defaults`, R22's two scripts. Nothing was run but the two
read-only reads of GitHub's run list I made at 20:34 (the same figures R22 reproduced). Context at the end: 58% (get_usage, 21:02 UTC).

## THE FOUR QUESTIONS OF R1, ANSWERED
1. DOES EVERY DEFAULT ACT AT THE FIRST TICK AFTER ITS DEADLINE, UNDER BOTH CLOCKS? YES. The review card's default is due
   `SILENCE_LEAD_H` (12) hours before the slot and runs at the first `expire_defaults` after it; `approve` keeps the slot while it is 30
   minutes away, so the window is 690 minutes against a longest measured gap of 661 (29 to spare) and against 56 with the backup clock.
   A default that found the video not clear is asked again at EVERY tick (`review_sweep`, `eye_sweep`). The Short's gate finishes a
   waiting row at the first tick at or after its cap (`test_a_late_tick_still_finishes_a_short`; its break is a tick that skips an old
   row). The long video's gate: with the guard (75) above the working clock's longest gap (56) and the lead (90) above it too, the next
   tick always comes before the video is public, until the cap. The two pushes, `alarm_retry`, `expire_defaults`: none acts only inside
   a window of minutes (R22 (6)). THE ARITHMETIC, CHECKED LINE BY LINE AGAINST `long_step`: both worked tables are right (13:46 -> 15:15,
   14:42 -> 16:00, 15:38 -> 16:30 the cap; the pull at 14:42 to 15:00; 13:07 none, 13:37 -> 15:00, 14:07 -> 15:30, 14:37 -> 16:00,
   15:07 -> 16:30), and so are the test's figures (a slot 26 hours ahead: 14; with the cell "3": 23 and the floor's cap 20; switch
   off: 20 and 8.5). The break "the guard back to 45" is caught by the walk that starts at 13:35.
2. IS ANY GUARD LOOSENED (item 146)? NO. `clear_to_post` judges the video at the approval with every read it has; nothing is made
   public unread - R22 (4) only delays a BLOCK and the Short stays private meanwhile; the HD guard is raised, the cap is not moved.
   What grows is the time a video stands SCHEDULED before its slot (12 hours, where it was 1.5): in it a pause, his KILL and his
   "Take it down" act as on every video after the first three - no guard that held a waiting video is skipped.
3. IS HIS REAL WINDOW TO LOOK SHORTENED UNSAID (items 150, 156)? NO, AND IT IS SAID TO HIM: the card's last sentence names the hour
   his silence is taken and that he can still stop it until the slot; the `decided_post` row carries "Take it down" and the Studio
   link; a moved slot is told with both slots. His tap starts its own job and waits for no tick.
4. IS ANYTHING NEW BUILT (item 186)? NO. One cell; two defaults moved; a count of empty reads kept in an existing column; words; seven
   tests with their breaks, all in steps 8, 9a and 10. What would be new (a late road on the slot's own day, a longer wait inside the
   Short's job, a message when the clock turns slow) is NOT built and is written as open issues with the figures.

## THE TEN QUESTIONS OF 5.4, IN ONE LINE EACH
1 serves him and a viewer (a first video on its Saturday; HD before public): yes. 2 his words (150, 156, 169, 180, 186): yes. 3
enforceable: yes - each block has its test and its break. 4 no taste by a model: none. 5 judged on what happened: yes - 1,761 slots
tried on 20 measured days, both rhythms worked. 6 money: none. 7 reuse: yes - `eye_hours`' own arithmetic, ONE cell for B-OWNER, the
floor's card and V4b's pair. 8 older pins: `tests/test_v12_floor.py` 675-678 passes unchanged with the switch off (on R22's word).
9 the worst still possible: a video whose silence comes after its slot goes out a week later, told to him - with the cell at 12 no
measured gap reaches it. 10 reality: the clock's proof in runs (R22 (8)); what `definition` reads; the minutes at the pilot.

## TWO POINTS FOR R1 TO RULE - NEITHER HOLDS THIS APPROVAL; THE EXACT WORDS ARE READY FOR EITHER RULING
A. THE SHIPPED VALUE OF `HD_GATE_ON` (R22 (5), line 959-961). As written: TRUE in `core.DEFAULTS`, and the pack sets it FALSE on the
   live Sheet until the clock's proof passes. A MISSED PACK LINE then leaves every Short private for hours on an unproven clock (a
   median of 197 minutes, 653 at worst - "against the gate's own purpose", R22's own words), and so does a buyer's first install,
   which runs on GitHub's schedule alone (02 item 70). The other way fails SAFE: a missed line is "public at its upload, as today".
   The repo's rule is a safe default for a new switch; R1-28 (5) ruled for V4b that a pack line is no cure where a setting removes
   the fault. IF R1 RULES THE SAFE DEFAULT, the words are - in line 960-961 REPLACE "In code the default stays TRUE: the suite, the
   sweep and the rehearsal walk the gate." WITH "In code the default is FALSE - the safe value on a clock nobody has proven:
   `tests/test_v12_hdgate.py`, the sweep's runs with the organisation on and the rehearsal set the cell TRUE themselves, so the block
   walks the gate as before; the pack's step sets it TRUE on the live Sheet when the clock's proof passes." and in line 1143 REPLACE
   "`HD_GATE_ON` FALSE (R22 (5)) and the launch is not armed" WITH "`HD_GATE_ON` stays FALSE, its shipped value (R22 (5)), and the
   launch is not armed". Typed in step 9a (the cell) and step 12 of B-OWNER (the sweep's and the rehearsal's setting). IF R1 RULES
   "AS WRITTEN": nothing moves, and R11's pack carries "set `HD_GATE_ON` FALSE" as a numbered step BEFORE the first Short.
B. THE TWO DAILY JOBS THAT RUN ONLY INSIDE ONE HALF HOUR (R22's open issue (c); `manage.py` 241-250: the key-expiry check with the
   model switches whose date has come, and the occasion's heads-up). R22 leaves them as an open issue (item 186) and told R1 (P32):
   that is a right reading of "nothing new". SAID ALL THE SAME, because B-OWNER's morning message leans on the first: with the backup
   clock a tick falls in that half hour on about three days in five, on GitHub's schedule alone on about one in fourteen - a key
   could expire unannounced. IF R1 RULES IT INTO STEP 10 (which already types `manage.tick`), the smallest words are: "the two daily
   jobs run at the FIRST tick at or after their hour, once a UTC day - line 243 becomes `if now_utc().hour >= 8 and
   S("EXPIRY_CHECK_DAY") != now_utc().strftime("%Y-%m-%d"):` and its block ends with `set_setting("EXPIRY_CHECK_DAY", ...)`; line 249
   the same at 9 with `OCCASION_DAY`; two auto cells; ONE test: a day whose only ticks are at 03:10 and 14:40 UTC runs both jobs
   once, at 14:40; a second tick that day runs neither. Break: the day's cell not written (both run at every tick)."

## THE ONE SENTENCE R1 ASKED ME TO JUDGE BY NAME (21:05 UTC): MAY THE FINDING AGAINST `floor.eye_hours` CLOSE BEHIND `TWO_SCREENS_ON`?
YES - IT MAY, AND HERE IT MUST; BUT FOR A REASON THE BLOCK DOES NOT YET GIVE, AND ON TWO CONDITIONS.
THE REASON. A lead of 12 hours is safe for him only TOGETHER with two things that exist only with the switch on: `clear_to_post`
(`_approve_eye` asks `approve_by_silence`: R17 (7 b)) and the `decided_post` row with "Take it down" until the slot - R22's own
ground for "his window is not shortened". With the switch off `_approve_eye` calls `approve` directly and sends no such row
(`floor.py` 447-452 as accepted): an unconditional 12 would take his silence ten and a half hours earlier on a film the floor could
NOT judge, with no button to stop it afterwards - one fault of the older path (a week late on a slow clock) traded for another (his
real window shortened, unsaid: items 150, 156). So the fix belongs behind the switch that carries its other half. The block's own
reason - "so `tests/test_v12_floor.py` 675-678 passes unchanged" - is the weaker one and is not the ground: a pin may move by design.
THE TWO CONDITIONS, in exact words (they hold no approval; R22 or the clerk inserts them):
(i) IN line 718 REPLACE "SAID PLAINLY: `TWO_SCREENS_ON` FALSE brings the 1.5 back with the rest of the older path." WITH "WHY BEHIND
    THE SWITCH, SAID PLAINLY: twelve hours are safe for him only with `clear_to_post` and the `decided_post` row's "Take it down",
    and both exist only with the switch on; unconditional, the older path would take his silence ten and a half hours earlier with
    no button to stop the film afterwards. So `TWO_SCREENS_ON` FALSE brings the 1.5 back with the rest of the older path - AND THE
    FAULT WITH IT: on a slow clock a film the floor could not judge then goes out a week late. The finding is closed for the
    shipped state only: its line in `reviews/V1c_audit.md` reads "CLOSED with `TWO_SCREENS_ON` TRUE: <commit>; with the switch off
    the literal stands (B-OWNER's memo, PART 7)", never a plain CLOSED."
(ii) FOR THE PACK (R11's brief, one line): "`TWO_SCREENS_ON` is never switched off at or after the launch: with it off a video the
    first-viewer check could not judge is approved an hour and a half before its slot and, on a slow clock, goes out a week late."
SO: nothing of `tests/test_v12_floor.py` 675-678 changes, and the cell is read behind the switch, as R22 wrote.

## TO CORRECT AT THE INSERT (one line; it does not hold the approval)
Line 706, the card's text: "it is approved at <HH:MM, India time>" is hours early on GitHub's schedule alone. REPLACE "If you do
nothing it is approved at <HH:MM, India time> and goes public on its slot," WITH "If you do nothing it is approved by your silence
from <HH:MM, India time> on - at the pipeline's next run - and goes public on its slot,".

## WHAT IS SOUND AND SHOULD NOT MOVE
The measure reproduced by a second hand, schedule events only; twelve hours chosen from the slots tried (15.0%, 30.0%, 98.2%, 100%)
and not from a feeling; ONE cell for every silence that puts a video on a slot; the rule "the guard outlasts the clock's gap" with a
test that walks every first minute; three empty reads before a block; "armed only on a proven clock", the proof counted in runs; the
honesty of NOT BUILT and of the finding against accepted code.

## FOR V4b (my own review of record)
V4b's pair reads `SILENCE_LEAD_H` and names no second cell: `REVIEW_OF_RECORD_V4b.md`, ADDENDUM 2. Its pack line takes R22 (8)'s
proof word for word.

## THE SCOPE OF THIS APPROVAL, ADDED 21:09 UTC (clock read) - READ THIS BEFORE THE FILE GOES INTO THE RECORD
THE FIRST LINE COVERS THE MEMO AS IT STOOD AT 144,974 BYTES / 1,220 LINES (40 marks "R22 (", R22's first change of 20:58 UTC) AND
NOTHING LATER. R22 changed the memo again at 21:07 UTC - now 151,678 bytes / 1,273 lines, 53 marks, nine places by its own word
(`diff PREDESIGN_B_OWNER.before_R22b.md PREDESIGN_B_OWNER.md`): "R22 (2 b)" TURNED - `floor.eye_hours` reads the cell in BOTH states
of the switch, with three numbers of `tests/test_v12_floor.py` changed by design; "R22 (2 c)" - `await_approval`'s signature
(`default=None, expires_h=None`); "R22 (9)" and "R22 (10)" - two new blocks for step 3. NONE OF THE FOUR WAS READ BY ME: I stood at
61% of my window (measured 21:07), past my line. THEY NEED A REVIEWER WITH ROOM before B-OWNER's approval is whole.
"R22 (2 b)" AS IT NOW STANDS IS THE OPPOSITE OF MY SECTION "THE ONE SENTENCE R1 ASKED ME TO JUDGE BY NAME" ABOVE. Both readings
behave THE SAME in the shipped state (`TWO_SCREENS_ON` TRUE); they differ only on the older path: behind the switch, a film the floor
could not judge can go out a week late on a slow clock; in both states, his silence is taken ten and a half hours earlier there and
his only stop afterwards is KILL in the Sheet (the "Video scheduled" e-mail names it; no button). It is a choice between two faults
of a path the launch does not run on: R1 RULES IT. I do not insist on mine - what the record must not hold is both. If R1 rules
"in both states", my section above is overruled, its two conditions fall, and R22 (2 b) with its three changed numbers stands once
a reviewer has read it; if R1 rules "behind the switch", R22 turns (2 b) back and my two conditions go in.
RULED, 21:14 UTC (R1-39 (2), confirmed in R1-40): BEHIND `TWO_SCREENS_ON` - this file's own section of 21:05, as written. R22 turns
"R22 (2 b)" back to it by one script run: condition (i) word for word, no number of `tests/test_v12_floor.py` changed, the audit's
line in the form given there. So the record holds ONE reading, and the paragraph above about two readings is history.
OUTSIDE THIS REVIEW, AND SO NAMED: "R22 (2 c)", "R22 (9)" and "R22 (10)" - they are R24's, in `REVIEW_LATE_BLOCKS_B_OWNER.md`, which
goes into B-OWNER's review commit beside R18's file and this one. This file's first line covers everything else marked "R22 (",
with the three insertions R1-37 ordered in my exact words (point A, the safe default; point B, in step 10; the card's sentence).
VERDICT: APPROVED
# REVIEW_LATE_BLOCKS_B_OWNER - the blocks R22 wrote into `PREDESIGN_B_OWNER.md` AFTER both approvals: "R22 (2 c)", "R22 (9)", "R22 (10)", "R22 (11)", "R22 (12)", and R22's own lines around R19's condition (i) in "R22 (2 b)"
THE REVIEWER: pool session R24 `local_e81ecbc6-4ee5-4a39-907c-680e11daa116` (Fable 5.2; effort xhigh, set by R1 at 21:33 UTC), which wrote
nothing of the memo and nothing of its reviews. Briefed by R1 (BEGIN R24, 19 Nov 2026 21:48 UTC; brief: section "R24" of
`RESET_ROLE_BRIEFS.md`, its blocks "CHANGED 21:15 UTC" (i) and "ADDED 21:18 UTC"). Written 19 Nov 2026, 21:48 to 22:02 UTC (clock read).
REVIEWED: `PREDESIGN_B_OWNER.md` as it stands at 156,300 bytes / 1,311 lines against `PREDESIGN_B_OWNER.before_R22b.md` (144,974 bytes,
the copy R19 approved): THE WHOLE DIFF, 19 HUNKS, EVERY ONE READ - new lines 25, 46, 220, 222, 324-332, 358, 406-427, 525-540, 753,
761-778, 781-785, 788-793, 1026-1030, 1036-1049, 1101-1104, 1132, 1155-1164, 1234, 1236-1237. No hunk lies outside the five blocks,
the frame of (2 b), R19's three insertions and the lines that follow from them.
READ FOR IT. The plan's 5.3 and 5.4 (by Grep, whole). `REVIEW_R22_BLOCKS_B_OWNER.md` whole. R1-36 and R1-37 whole. Of the memo: lines
216-224, 244-261, 262-335 (PART 1's end, PART 2 with `mail`), 336-405 (the table with row 21; PART 3 with `_alarm`), 428-445, 503-526,
726-797 (PART 7's turned card), 876-950, 1016-1079 (PART 9: the Short's wait, the tests, the sweep's judges), 1120-1185 (the steps).
THE CODE (the tree at 5ca8c99, code d64fdcc): `manage.py` 59-86, 176-357 (`tick`, the two daily jobs at 241-250), 471-483 (`guardian`);
`caretaker.py` 1-75 and 130-139 (`policy_rescue`, `_policy_answer`, `expiry_check` with its seed, `register`); `notify.py` 1-150 whole
(`send`, `_deliver_now`, `answer`, `expire_defaults`); `contract.py` 995-1093 (`await_approval`, `approve`); `org/floor.py` 400-405;
`core.py` 430, 1071; `publish.py` 42-52, 81-87, 140-145, 186-287; `occasions.py` 114-122; `steward.py` 218-229; `tools/sweep.py`
186-269, 322-330, 428-446; `tools/rehearsal.py` 38-79; `tests/conftest.py` 1-60; `tests/test_v10_future.py` 5-29; `tests/test_v102.py`
64-74; `tests/test_v12_floor.py` 247-251 and 672-679; `tests/test_v89.py` 155-165; `proving/blocks/DRAWN.json` whole. BY SEARCH: every
`NT.send` of an alarm kind under `whatifs/`; every caller of `await_approval` under `whatifs/`, `tests/`, `tools/`; every test that
names `guardian`, `policy_rescue`, `expiry_check` or `heads_up`; every test file that calls a `tick(`. `git blame` of `manage.py`
243 and 249. The typist's two DESIGN QUESTIONS in `bowner_step_2a.md` (44-83).
**NOT READ, SAID:** the memo outside the lines above (its parts 4 to 6, 8 and 10 and its head: R18 and R19 read them); `models.ask`'s
retry loop (so I give no figure for the longest wait in block (9)); `tools/rehearsal.py` beyond 38-79; `occasions.slot_for`; the
typed patches of steps 3 and 4 (a review of the memo's words, not of the typing); `02` in the owner's own words (items 70, 149, 150,
156, 180, 186 stand here as the memo and R1's rulings quote them).
NOTHING OF THE PIPELINE WAS RUN: no test, rehearsal, sweep or break; no file of the repository touched; nothing committed. Two small
read-only scripts of my own compared quoted passages and counted anchors (below). `proving/next.py` once, at 21:33 UTC (state: DRAWN
in PROVING at d64fdcc; its card was the prover's - not this lane).
USAGE (`get_usage`, 21:59 UTC): context 48% (478,984 tokens - this body read V4b's memo and review whole as R23 for eleven minutes
before R1 moved it to R24); weekly Fable 60%, all models 34% (the pool's lines).

## THE VERDICT IN SIX LINES
1. ALL FIVE BLOCKS AND THE FRAME ARE APPROVED: each does what it says on the code as it stands, none loosens a guard (item 146),
   none builds a new part (item 186), and each has its test and its break.
2. R19's WORDS STAND WORD FOR WORD in every place they were ordered (checked by a script on whitespace-collapsed text, each passage
   found exactly once): condition (i) of (2 b) - 707 characters; point A's two sentences in (11) - 310 and 82; point B in (12) - 496;
   the card's sentence - 136. NO NUMBER OF `tests/test_v12_floor.py` IS CHANGED.
3. HIS RESUME TAP SURVIVES ON EVERY ROAD, AND THE ALERT IS ONE INCIDENT (block (9)). Followed on four roads below.
4. NO ROW IS SENT TWICE, AND A FAILED COPY IS LOGGED AND THE ROW STILL REACHES BOTH SCREENS (block (10)).
5. THE BLOCK STILL WALKS THE GATE (block (11)) - on the parts whose runs have the organisation on. ONE SENTENCE IS OWED THERE,
   BEFORE STEP 9b AND STEP 11 ARE TYPED: without it a typist who puts the counter `hd_gated` on the block's part with `--org off`
   (where every counter before it stands) turns the acceptance block RED for no fault of the code. Insertion 1.
6. ONE SENTENCE OF REASONS IN (12) STATES A FRACTION THE WRONG WAY ROUND (it is R1-37's sentence, copied). Insertion 2.
NEITHER INSERTION CHANGES A DECISION, A LINE OF CODE ALREADY TYPED, OR A STEP BEFORE 9b: B-OWNER's BUILD MAY BEGIN ON THIS FILE.

## THE INSERTIONS, IN EXACT WORDS (a clerk's script; every anchor was counted and stands EXACTLY ONCE in the memo at 156,300 bytes,
## whitespace runs matching any whitespace run; AFTER = the text is put right after the anchor, in the same line)
**INSERTION 1 - OWED BEFORE STEP 9b IS TYPED (block (11): where `hd_gated` stands).** AFTER
ANCHOR: both in `proving/blocks/B-OWNER.json`.
TEXT:  R24 (on R22 (11)): `hd_of` IS ASKED ONLY OF A RUN WITH THE ORGANISATION ON - the runs in which the sweep set `HD_GATE_ON` TRUE - AND THE COUNTER `hd_gated` STANDS IN THE BLOCK FILE ONLY ON PARTS WHOSE RUNS HAVE THE ORGANISATION ON, never on a part with `--org off` (part B of every block so far): there the sweep does not set the cell, the gate is off as shipped, a Short's `privacy` receipt holds no "public after", and `proving/verdict.py` reads a counter that does not EQUAL its part's n as RED. The typist of step 11 reads this sentence before the block file is written.
WHY IT IS OWED: with the default TRUE (R4) every run walked the gate, so the memo never had to say on which parts the counter
stands. R19's ruled words set the cell TRUE only in "the sweep's runs with the organisation on"; R22's "(it judges those runs)" says
the judge follows - but the block file is typed in step 11, which by R22 (7) "holds none" of R22's lines, and every block so far
carries its new counter on part B too (`proving/blocks/DRAWN.json`: parts A, B and C hold the same list; its own note says
`verdict.py` "holds only counters that EQUAL n"). Part B runs `--n 4 --org off`.

**INSERTION 2 - A FIGURE THE RIGHT WAY ROUND (block (12); R1-37 (3)'s sentence).** REPLACE
ANCHOR: a key could expire unannounced on three days in five even with the backup clock
TEXT: the check is missed on about two days in five even with the backup clock (R19: a tick falls in its half hour on about three days in five) and on about thirteen in fourteen on GitHub's schedule alone, so a key could expire unannounced
WHY: R19's point B measures how often a tick FALLS in the half hour (three days in five; one in fourteen); the sentence gave that
figure as the days the reminder is LOST. Read with `caretaker.expiry_check` (59: `0 <= left <= days`): a missed day is made good on
the next day the check runs, so what is lost is a reminder only when every day of its window is missed - rare with the backup
clock, about one time in three for the fourteen-day card on GitHub's schedule alone. The reason for the block stands either way.

**INSERTION 3 - WHAT THE CHANGE OF (12) REACHES BEYOND ITS TWO LINES, SAID ONCE (holds nothing).** AFTER
ANCHOR: call `expiry_check` and `heads_up` themselves, with their own dates).
TEXT:  R24: WHAT ELSE IT REACHES - every run that walks the real `manage.tick` on a fresh Sheet (a test, a sweep id, the rehearsal) now starts both jobs at its first tick whenever the clock it reads stands at or after 08:00 UTC (09:00 for the heads-up), where they started only inside one half hour. They write six rows on tab `Expiry_Calendar`; from 26 Nov to 10 Dec 2026 the seed "Claude Max plan" (10 Dec) also makes one `expiry` card on such a Sheet, and three days before an occasion special one `occasion` card. Neither is a fault, and no judge of today counts them (read: the five test files that call `MG.tick()`, `tools/sweep.py` 327 and 436, `tools/rehearsal.py` 38-79 - each asks for a kind, none for a whole tab). A test of this batch that counts a whole tab or a whole list after a real tick plants its clock outside those days.
WHY: the block says truly that no older test PINS the two lines; it does not say that the jobs now run in two thirds of the day
instead of one forty-eighth of it, in every run on the real clock. Whoever reads an `expiry` row in a sweep log on 27 Nov must
find its cause in the record.

**SEEN OUTSIDE MY FRAME, ONE LINE FOR THE TYPIST OF STEP 8 (holds nothing; the words are R19-approved text).** `floor.eye_hours`'
docstring begins "the cell, never past 1.5 hours before its slot" (`org/floor.py` 402); the memo replaces only its parenthesis, so
the function would still SAY 1.5 while it reads `lead`. AFTER
ANCHOR: becomes "the cell SILENCE_LEAD_H: a tick can be 11 hours late".
TEXT:  R24: and its words "never past 1.5 hours before its slot" become "never past the lead before its slot (SILENCE_LEAD_H with TWO_SCREENS_ON, else 1.5 hours)".

## EACH BLOCK, AGAINST THE CODE IT NAMES
**"R22 (2 c)" - APPROVED.** Today `await_approval(..., default="stays private", expires_h=72)` (`contract.py` 1061). The block makes
both `None` and fills each ON ITS OWN when it was not passed: the switch on -> the hours of R22 (2) and "approved by your silence";
off -> 72 and "stays private". EVERY CALLER READ: `episode.py` 964 passes neither (the reviewed video: computed, as wanted);
`episode.py` 966 and `tests/test_v12_floor.py` 686, 703, 714, 1003 pass both (the floor's card keeps `eye_hours` and its own words);
`tests/test_v102.py` 70 passes neither and runs with the switch off (conftest's autouse list once `OLD_SCREENS` is in it): 72 and
"stays private", unchanged. No caller passes one without the other. AGAINST R19's ADDENDUM 2 FOR V4b: it is the same reading - V4b's
pair calls it with no hours, names no second cell, and `SAL.silence_h` is not typed. A pair video pulled back inside its last twelve
hours gets the floor of one hour (`max(1.0, ...)`), then `clear_to_post` judges it: no road gives it a time unjudged.
**THE FRAME OF "R22 (2 b)" - APPROVED.** Condition (i): word for word (line 2 above). The lines around it: `lead = S("SILENCE_LEAD_H",
float) if S("TWO_SCREENS_ON", bool) else 1.5` replaces the 1.5 of both lines of `eye_hours` (404 and 405: there are exactly two).
`core.py` 1071 holds the words "never past 1.5 hours before its slot" exactly as quoted, and the new words read true in both states.
`tests/test_v12_floor.py` 247-250 pins that cell's VALUE ("20"), 675-678 pins 20, 8.5 and 1.0 with the switch off: both unchanged.
THE TEST's FIGURES, WORKED: a slot 26 hours ahead - the review card min(72, 26 - 12) = 14 and `eye_hours` min(20, 14) = 14; with the
cell "3" - 23, and the floor's card 20 (its own cap); the switch off - min(20, 24.5) = 20, and min(20, 10 - 1.5) = 8.5. Right.
`test_a_tick_eleven_hours_late_keeps_the_slot` for BOTH cards: the default due at slot - 12 h, the tick 11 hours later stands one
hour before the slot, `approve` keeps a slot that is 30 minutes away (`contract.py` 1081). Right.
**"R22 (9)" - APPROVED. HIS RESUME TAP ON EVERY ROAD, THE ALERT ONCE:**
(a) THE ORDINARY ROAD, the switch on: `policy_rescue` -> `send("policy", ..., three buttons)` -> `_alarm`, no open incident -> ONE
    row, count 1, Discuss / Build fix / Resume now, pushed at once; it returns the id; `mail(..., screens=not aid)` is then the copy:
    the e-mail as today, no row, no second count. (Two e-mails go, as two go today: the urgent card's own and the plain one.)
(b) THE CARD FAILED (`policy_rescue` raised or gave no id): `mail(..., screens=True, buttons=[("Resume now", "RESUME")])` -> `send`
    -> `_alarm(mailed=True)`: ONE row, count 1, with "Resume now" (a caller's button, so no "Seen"), pushed, not mailed twice.
(c) A SECOND FIRING THE SAME UTC DAY: the card meets its own open incident, `_alarm` counts it and returns that id, the mail is the
    copy: one count a firing, the first firing's three buttons kept.
(d) THE SWITCH OFF: `mail` is `PUB.email`; only the order of the two e-mails turns. `tests/test_v10_future.py` 9-16 reads the
    card's row and its BUILDFIX answer, never the order: unchanged. No other test calls `guardian` (searched).
ON ALL FOUR `caretaker._policy_answer` (33-36) answers RESUME for the KIND, whichever firing made the row (`register`, 137-139);
the pause and the hold of scheduled videos are set BEFORE either message (`manage.py` 474-475). THE CLAIM "`policy` is the only alarm
kind both mailed and sent with buttons": TRUE - the `NT.send` sites of alarm kinds are `policy` (three buttons), `risk_lock`,
`risk_gone`, `org_watchdog` (sent, never mailed) and `kids_flag` (`publish.py` 143: no button, as the block says).
SAID FOR R1, IT HOLDS NOTHING: on this ONE road the alarm now waits for `policy_rescue`'s model call - as the urgent card does
today - where the memo's first order would have pushed the buttonless row before it. The block says so plainly. I looked for a
smaller way inside `guardian` that keeps both (the push before the model call AND the three buttons with the note) and found none:
either one event counts 2 and the note is cut to `last_text`'s 300 characters, or `_alarm` or `policy_rescue` must change. What
protects the channel - the pause - never waits. The block's choice is the right one.
THE BREAK is caught: the old order with the old call leaves "Seen" only (the buttons assert fails); the old order with the new call
leaves count 2 (the count assert fails).
**"R22 (10)" - APPROVED.** IS A ROW EVER SENT TWICE? No: `mail` makes one `send`; with a raise it passes `mailed=False`, which sends
no second ROW - for an alarm it lets `_alarm` try its own "URGENT" mail in its own try, for every other kind (tier "week") nothing
is mailed again. IS A FAILED COPY STILL TOLD? It is logged as a warning with the subject, the house's way (`_deliver_now` 98 does
the same today), and the message itself reaches both screens - which is the point of item 149. With `screens=False` and a raise it
returns False: rows 10, 16 and 37, and row 21 when the card stands, then lose a copy whose message the screens already carry.
ONE CONSEQUENCE, SAID: a caller that writes its "sent" mark right after the mail (`manage.py` 303-304, 313-315) now writes it even
when the copy raised, so that e-mail is not tried again - right, since the row was sent; today the same raise would have ended the
tick. The switch off: today's call, raising as today; `tests/test_v89.py` 162-165 (a mail that raises -> `pr_ready` is None) runs
there and passes unchanged. The break (the try removed) is caught by the first clause of the test.
**"R22 (11)" - APPROVED, WITH INSERTION 1.** R19's two sentences: word for word, in R22 (5) and R22 (8). DOES THE BLOCK STILL WALK
THE GATE? YES: `tools/sweep.py` 203 and 262 are the two loops over `TEST_SETTINGS` (short mode and produce mode; that dict is not
changed), the third mode calls the rehearsal, which sets the cell itself beside its line 61 - BEFORE its two Shorts are made (63),
so "HD gate: k of k uploads" is walked. `--org` defaults to "on" (453), so the block's short parts D and E and the parts A and C walk
it. Step 9a and 9b: at 9a's commit neither tool has a judge yet (9b types the judges, the counters and the setting together), so
"between the commits both run with the gate off and stay green" is true. UNDER PYTEST THE DEFAULT IS NEVER WHAT A TEST RUNS ON:
conftest's autouse list sets `HD_GATE_ON` FALSE for every test (the entry of `OLD_SCREENS` stays), so the fixture `gate_on` is what
every gate test needs whatever the default - and `test_the_gate_is_off_until_it_is_armed` catches its break by the literal
`core.DEFAULTS["HD_GATE_ON"][0]`. A test in another file that walks the gate (step 10's two) takes the fixture by import or sets
the cell the same way: a typist's line, no choice in it.
**"R22 (12)" - APPROVED, WITH INSERTIONS 2 AND 3.** R19's words: word for word. THE TEN LINES OF CODE (`manage.py` 241-250): both
jobs stand in a try of their own and AFTER the paused branch's return, BEFORE the voice branch's early returns - so the test's two
planted ticks reach them on a fresh Sheet. ONCE A DAY HOLDS EVEN IF THE DAY's CELL IS NOT WRITTEN (a job raised before its
`set_setting`): `expiry_check` marks each card on its row (`reminded`) and `heads_up` sends under one key while its card is open,
so a second run the same day sends nothing new - the break "the cell not written" is caught by the test's count, not by a second
card. The UTC day of the cell is the UTC day both jobs compute with (`now.date()`): no card moves to another day. A card that
falls into his quiet hours is queued by `_deliver_now` as today. "No older test pins the two lines": TRUE (`tests/test_v10_future.py`
25-28 and `tests/test_v10_growth.py` 200-202 call the functions with their own dates). "Both lines came with the upload of 8 Nov
2026 (6accea7)": TRUE (`git blame`). The two auto cells enter in step 10 with their first reader: R18 (1)'s rule kept.
THE LINES THAT FOLLOW (46, 1101-1104, 1132, 1155-1164, 1236-1237): each agrees with its block; the test counts add up against the
size table (3: 6 + 2; 8: 12 + 3; 9a: 9 + 3; 10: 6 + 3).

## THE TEN QUESTIONS OF 5.4, ONE LINE EACH, FOR THE FIVE BLOCKS
1 serves him: yes - his Resume tap, a message that cannot be lost with its copy, a gate that cannot hide a Short on an unproven
clock, a key that cannot lapse unannounced. 2 his words (70, 149, 150, 156, 180, 186, as quoted): yes; item 180 on (9) is said
above. 3 enforceable: yes - five tests, five breaks, each break caught. 4 no taste by a model: none. 5 judged on what happened:
yes. 6 money: none. 7 reuse: yes - `_policy_answer`, `eye_hours`' arithmetic, the sweep's own `set_setting`. 8 older pins: named
and right (`test_v10_future` 9-16, `test_v102` 70, `test_v89` 157-165, `test_v12_floor` 249-250 and 675-678). 9 the worst still
possible: none of the five lets a video out; the worst is a proof turned red by a counter on the wrong part - insertion 1.
10 reality: the longest wait of the policy alarm behind its model call, at the pilot's first policy watch.

## THE THREE PLACES I ATTACKED HARDEST, AND WHAT I FOUND THERE
(1) THE POLICY ROAD, every order of the two messages with and without the switch, and the card failing: his Resume tap holds on
all four; one incident. (2) WHAT A DEFAULT OF FALSE DOES TO THE PROOF - conftest, the three modes of the sweep, the rehearsal, the
block file's parts: the gate is walked; the counter's place was unsaid - insertion 1. (3) THE TWO DAILY JOBS BEYOND THEIR TWO
LINES - who else walks the real tick, what the jobs write there, and the figure given as the reason: insertions 2 and 3.

## WHAT IS SOUND AND SHOULD NOT MOVE
`screens=not aid` - one line that makes the mail a copy exactly when the card stands; the row sent whether or not its copy went;
the safe default with the tools arming the gate themselves; "the first tick at or after the hour, once a UTC day" with a day cell;
`await_approval` computing the hours itself so that no caller can pass a lead of its own.
