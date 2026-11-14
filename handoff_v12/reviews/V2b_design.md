VERDICT: CHANGES REQUIRED
# V2b INSIDE THE FORMAT - design review, round 1 (14 Nov 2026)
The reviewer: a fresh Fable 5.2 session (Effort High) that did not write the memo (the plan's 5.4, AMENDMENTS 1 AND 2, session 2 of the chain).
Reviewed: the record of V2b in `BUILD_STATE.md` (steps 1 to 3) as of commit 58c6167, base 5827d97.
Read for it: the plan whole; the handoff `CLAUDE.md`; `02` whole; the redesign 4.1, 4.6, 10.7, 11.4, 11.10 with its end notes; in `BUILD_STATE.md` the head
line, the standing rules, the owner's verdict, NEXT down to "what V2d-b leaves ready", the whole record of V2b, open issues 60, 69, 74, 75, 77, 101, 124,
125, 129, 177, 185 to 190; and the code: all of `formats.py`, `org/audience.py`, `org/layman.py`, `enforce.py`, `cta.py`, `shotplan.py`, `immersion.py`,
`overlay.py`; `room.py` (`run_room` to `ensure_tease`, `_director_extra` to the end); `episode.py` (`_stage_plan`, `anchor_shots`, `_assets`, `Job`, `_render`,
`produce`, `_strip_beats`); `render.py` (the camera library, `parallax_segment`); `motion.py` (`merge`, `place`, `carry`); `voice.py` (`parse_script`, `narrate`);
`contract.py` (`p_asks`, `p_tease`, `p_living`, `p_format_kept`, the table, `run`); `prompts.py` (BIBLE, WRITER, DIRECTOR); `engage.py` (`brief`);
`format_engine.check_script`; `hooks.run_hooks`; `ladder.enter` / `pitch`; `truth.unread_settings`. The memo's four passages were counted with the repo's
own regexes (a read-only script in the reviewer's scratchpad; nothing of the pipeline was run).
USAGE: at the start the 5-hour window 7%, weekly all models 2%, weekly Fable 4%, context 9%; when this file was written 10%, 3%, 6%, context 45%.

IN ONE PARAGRAPH: the design is the right one (D: the inside of a format is data that code executes) and most of it can be typed as it stands. But
six sentences of the memo are not true of today's code, and typed as written they give the opposite of what the batch is for: the whole film
becomes ONE act in ONE place and every check passes (change 1), each act is given the NEXT beat's place (2), ordinary story sentences are deleted
from the script as "asks" (4), every offline F1 film fails its own ending check (5), and a writer is told to open on the word "you_pov" (12). A
typist that decides nothing would type exactly that. Nothing below asks for a new rule; every change makes a rule of the memo true or typeable.

## The ten questions of 5.4
1. Does every part serve a viewer or the scoreboard in a way a layman could name? YES, with two parts that are machinery until a picture proves them -
   the place sentence in front of a prompt (the Director who writes the picture is never told the place: change 10) and the `sign` that `camera_shown`
   compares with the plan it came from (true only once the parallax side follows it: change 9).
2. Does it honour every word of the owner that touches it? NO - item 16 ("so many stats", "no audience feel", the name label) and item 19 (first person,
   layman) are served; item 19's "continuous camera" is honestly narrowed (CHANGED FROM THE REDESIGN 1); but open issue 74's EMOTION BEAT - a scope line
   of NEXT's "V2b's scope" - is not in the memo at all, and `engage.brief` still tells every F1 and F3 writer to use audience prompts and to place the
   emotion beat "just before the verdict" (change 13); items 12, 14, 15 (hard enforcement) fail where a check passes on a film that is one act (change 1).
3. Is every rule ENFORCEABLE as written? NO - six are not: the unit's beat (1), the place of an act (2), an act's first picture on screen (3), the ask
   recogniser used to delete and to hold (4), the ask-free window on a short film (5), the last line (6); and the camera rules under `CAMERA_MOTION`
   "gentle" and after a re-render (7, 8).
4. Does any rule judge TASTE by a cheap model, or let a model's opinion gate a video? NO - every measure is a regular expression, a count or the render's
   own record; designs B and C were refused for exactly that reason.
5. Is each measure judged on the finished file / the render's record, and does each new limit have BOTH kinds of measured pairs? NO - `camera_shown`
   reads the record (good), but the record goes stale after `Job.rerender_times` (8); the floor of F1 has both pairs, with hand counts that are wrong
   (change 14: GOOD-1 is 10 of 11, GOOD-2 is 10 of 15 = 66.7%); the floor of F2 (30) and the run limit 4 for a four-voice trial have NO good trial
   passage, and 30 lies under the 40 the memo itself calls bad (change 15).
6. Money: is every new paid second or call a line, inside Rs 5,000? YES for what the memo names (no new call; the writers' fix rides in the one
   `writing` line of `costguard.lines`) - and NO for two things it does not name: in F3 `room.format_pass` makes a PAID fix call, twice a video,
   that asks for the second voice the format forbids (change 13), and "never beyond the budget" for an act's first picture trades a still of
   under Rs 1 for a held video (change 11).
7. Does it reuse what earlier batches left ready? YES for the pattern (`audience` / `layman`: a pure measure, the ONE fix, the check; `segmeta`; the
   format row) - NO for the one warning of the brief's READY line: "`place` decides WHICH stills move - a camera-path rule that wants a say goes
   through it or runs before it". `path.lay` runs AFTER `motion.place` and has no say (change 3). And it writes a second speaker parser beside
   `voice._peel` (change 14).
8. What does it change that an OLDER test or check pins, and is each change named? PARTLY - named: `OLD_INSIDE`, the three shares, `kept_report`,
   `p_tease`, `p_living`, `prompts.WRITER` byte for byte for a trial. NOT named: `ctx["states"]` is a list of 5-tuples that `p_visual_change` unpacks
   (`for a, b, typ, clip, short in ...`) - four more fields "inside" it break that check; `audience.shape`'s inner helper `still` (PROTECTED file) must
   be lifted to be reused; `voice.parse_script` / `Unit` / the timeline entry change for every caller of `narrate`; `p_living`'s chip rule must be
   silent with the switch off or every older test with a speaker tag turns red (change 16).
9. The worst video this design could still let through, and which check holds it? AS WRITTEN: an F1 film that is one act - every picture prefixed
   with ONE beat's place (beat 0 + 1: "your bathroom"), under a story that goes from the bathroom to the street to the planet - passes `camera_path`
   ("1 acts in 1 places") and `camera_shown`; nothing holds it (changes 1, 2). AFTER the changes: a lecture with a throwaway "you" in every sentence ("as you know,
   gravity is ...") passes `viewer_inside` at 100% - the memo says so itself and hands it to V1c's floor (open issue 185): accepted, it is said.
   And a Director whose own prompts name five places inside one act passes on the prefix - open issue 186; change 10 narrows it for the price of a paragraph.
10. What can only reality answer, and is it written down for the pilot? MOSTLY - 185 to 188 and 190 are right. MISSING: a trial made without approved
   cast art now has four voices, nobody on screen and no chip - can a viewer tell who speaks (his ear at the pilot); the floors and the run limit of
   F2 (185 names F1 and F3 only); whether `kind_of_text` meets a real script without deleting a story line (change 4 makes it a test first).

## The changes (each is "the memo must ..."; ordered by what a viewer would suffer)
1. THE UNIT'S BEAT - the sentence about `voice.py` is false, and the batch stands on it. `episode._stage_plan` hands `narrate` the script AFTER
   `episode._strip_beats` removed every line that starts with "##" (lines 150 to 153 and 160 to 161); `voice.parse_script` never sees a heading (if it
   did it would SPEAK it: `_peel` strips the "#" and keeps "BEAT 2"). A counter typed "where the script is cut into units" counts nothing: every unit is
   beat 0, `path.acts` is ONE act, every picture of an F1 or F3 film gets ONE place, and `camera_path` and `camera_shown` both PASS. The unit test the
   memo asks for ("a unit knows its beat") would pass on a script with headings while the production strips them first. (`_strip_beats`' own `marks`
   cannot be used either: they count LINES and are used as unit indexes, and a line of three sentences is three units.) The memo must say exactly
   how a unit learns its beat - the function, who passes what (both `narrate` calls of `_stage_plan`, and every other caller of `narrate` and
   `parse_script` found by search with what it passes), that a heading is never spoken, that `reactions.ensure_units` and `audience.breathe` keep
   the field - and must demand on a WHOLE F1 production: the units carry at least two different beats, the PASS words of `camera_path` name at
   least two places, two pictures of different acts carry different place sentences; and a deliberate break ("the heading never reaches the
   counter") that this whole-production test catches.
2. THE PLACE IS OFF BY ONE. 3.1 says a heading "raises `act` by one (act 0 before the first heading)", so the units under "## BEAT 1" carry 1; 3.2
   takes "the bible beat whose `n` equals the act's first beat + 1" = beat 2 (`prompts.BIBLE`: `"beats":[{"n":1,...}]`). Every act would be told the
   NEXT beat's place and the last act none. (`hooks.apply_to_script` puts the hook AFTER the leading heading, so no unit sits before it.) The memo
   must give one convention - best: the number written in the heading when it has one ("## BEAT 4" is 4: a real writer may skip or merge a beat),
   else the headings counted from 1, 0 before any - and `place_of` = the bible beat whose `n` EQUALS it; with a test on the offline bible that the
   act under "## BEAT 1" gets beat 1's `visual_world`.
3. AN ACT'S FIRST PICTURE CAN BE PAID AND NEVER SHOWN - then `camera_shown` holds a finished, paid film. "Since the first still of every act then
   has a picture of its own, the nearest earlier picture of any later still of that act is a picture of that act" is false twice. (a)
   `motion.merge`: a line shorter than `UNIT_MERGE_SEC` (1.0 s: "Step outside.", "Look up.") gets no picture state - `_render` `continue`s BEFORE
   `prev_img` is set (lines 433 to 436), so the stills after it show the act BEFORE's picture. (b) `motion.place` runs BEFORE `path.lay` and knows no
   act: a scene reserves, and a living clip covers (`room_s`, `covers`, `carry`), the plain stills that follow - also the first still of the NEXT act;
   covered whole it is merged away the same way, and the viewer hears the new act over the old place. The memo must decide and write, with a
   test for each case (a 0.6 s first line of an act; a living clip bought on an act's last line) and a break: what the film shows on an act's first
   line when that line is merged or covered, and how the act's own picture still becomes the picture its later stills show (for example: the acts
   are computed BEFORE `motion.place` - they need only the units - `motion.plain` is false for an act's first picture so that no clip runs into it,
   and `_render` takes `own` as `prev_img` / `prev_i` before its `continue`). The brief's READY line said it: a camera-path rule that wants a say goes
   through `place` or runs before it.
4. THE ASK RECOGNISER DELETES STORY LINES. `cta.kind_of_text` was written to decide whether an ask is already there - a wrong yes cost nothing. 3.3
   uses it to DELETE lines (`cta.strip`, three call sites) and to HOLD a video (`format_ending`'s window). Measured on ordinary first-person
   sentences: "Nothing like this has ever happened to you." = like; "You have never felt anything like it." = like; "Would you like it to stay?" =
   like; "You send it spinning across the room." = share; "You want to tell your friend, but your phone is floating too." = share; "You cannot share
   it with anyone." = share; "You text it to your sister." = share; "Your newspaper subscription is the last normal thing left." = subscribe. In F1
   (keep subscribe) and F3 (keep nothing) each such line would be cut out of the narration without a word - the lesson of V1b and V2c-a, in a
   function that removes. And what F3's own brief forbids ("comment or follow") is NOT recognised: "Tell me in the comments what you would do."
   = None. The memo must define the recogniser that `strip` and the window use - exact patterns, so narrow that a line is an ask only when code can
   RECOGNISE one (a line the code itself inserted from `POOLS` / `TRIAL_POOLS`, or an imperative to like, subscribe, share or comment) - give
   the eight sentences above as test data that must survive `strip` and must not fail `format_ending`, say what happens to the second line of a
   two-line ask ("Please don't call it democracy." left alone is a reply to nothing), and limit `overlay.CtaChip` to `formats.asks()` when
   `ENDINGS_ON` (today a LIKE chip would pop up over "nothing like this" in a film that asks for no like).
5. THE ASK-FREE WINDOW SWALLOWS THE CODE'S OWN ASK. `cta.ensure` puts F1's subscribe ask at 65% of the lines; `format_ending` forbids any ask in the
   last `ENDING_FREE_S` = 40 SECONDS. On an offline film (75 to 105 s; the memo's own example is 82 s) 65% is second 53 and the window starts at
   second 42: every F1 film of the tests, the rehearsal and the sweep fails `format_ending` by the memo's own arithmetic, and the builder would have
   to choose between moving the ask and shrinking the judge (L7). "Outside the tail" is true of `strip`'s 12% of LINES, not of the check's 40 s.
   The memo must give ONE definition used by both (for example: the last `min(ENDING_FREE_S, 12% of the voice's length)` seconds, on the units'
   own start times - units, not script lines, carry times), show the arithmetic for 82 s and for 510 s, and say that what `strip` leaves and
   `ensure` adds can never fail the check (a test).
6. THE LAST LINE RULE HOLDS GOOD ENDINGS. It judges the last COUNTED sentence (four words or more) and wants the word "you" inside it. "Would you?",
   "Keep it?", "Would you stay?" (three words) are not counted, so the sentence BEFORE is judged and a film that ends on the very question the
   format asks for is held; "Keep it, or give it back?" has no "you" and is held. The same for F3's arrival ("You're home."). The memo must
   judge the last SPOKEN sentence whatever its length, and look for the viewer in the last spoken line (or its last two sentences), with those
   four endings as tests that pass and "Subscribe for more." / "Next simulation: ..." as tests that fail.
7. `CAMERA_MOTION` = "gentle" IS A LEVER OF D6 (`levers.LEVERS`, `registry` D6) - a ticket can set it. Then `parallax_segment` returns through
   `_parallax_v87` before `pick_move`: the move is drawn from push / pull / pan_l / pan_r / rise / drift with a random side, `_LAST["move"]` stays
   None, and EVERY F1 and F3 film fails `camera_shown` ("move not in path.MOVES") after its pictures are paid. The memo must say what a path format
   does under "gentle": the older mover takes `sign` and a pool too and records its move, or the lever is refused / ignored for a path format, or
   the check says NA with its reason - one of them, with a test.
8. THE RECORD MUST STAY TRUE AFTER THE RENDER. (a) `Job.rerender_times` (the fix for a black or frozen stretch) re-draws a still with
   `parallax_segment(..., detail=True, focus="center")` - no sign, no pool - and leaves `segmeta` as it was: the film may show a `pull` while the
   record says `drift`, and `camera_shown` passes on the stale line. (b) A segment that fell back (`drawn_` False: `graphic_segment` on the picture)
   would be recorded with the PREVIOUS segment's move. The memo must give `rerender_times` the state's sign and pool and make it rewrite `move`,
   record "" for a fall-back state and say what `camera_shown` does with it, and name where the four fields travel: NOT inside `ctx["states"]`
   (5-tuples that `p_visual_change` unpacks, and None when the motion ladder is off) - a key of their own.
9. "ONE DIRECTION OF TRAVEL" IS NOT WHAT `sign` DOES YET. In `camera_path` the side of the depth parallax is a second, independent draw
   (`par_px = sw * par * rng.choice([-1, 1])`): on `push_parallax`, `orbit` and `whip_settle` the near things slide left or right at random whatever
   `sign` says; `push_parallax` and `handheld` have no sideways travel at all. The memo must make `par_px` follow `sign` when one is given (and keep
   every draw of the old path byte for byte when it is None - the reference frames), and write the two pool expressions exactly: with a pool the
   high-energy choice is `[m for m in MOVES_HIGH if m in pool and m != avoid]`, the calm one the same over `MOVES_CALM`, the fall-back
   `list(pool)` minus `whip_settle`, never `list(MOVES_CALM)`; a suggested move outside the pool is refused.
10. THE DIRECTOR IS NEVER TOLD. The picture's words are the Director's (`prompts.DIRECTOR`, `immersion.director_rules`): "concrete subject, camera,
   lens", "extreme wide lens, motion blur", `"pov": eyes|object|hands|helmet|vehicle|ground`, `camera` = ... pull | kb_roll. The memo puts "ONE
   PLACE FOR THIS ACT: ..., seen at eye level." in front of a prompt that may go on "aerial view of the city, 14mm" - the picture model gets two
   orders and the check reads only the first. The memo must add, word for word, a paragraph to the Director's brief in a "path" / "walk" format
   (where `_immersion_notes` is; `formats.block("director")` or `path.director_rules()`): every picture from the viewer's own standing height, never
   from above, from outside or from an object; every beat stays in the place its `visual_world` names; no `pull`, no `kb_roll`; and say what the
   three animated scenes' motion sentence is in a walk ("camera mounted on the moving object, accelerating, shaking" is today's, in every format).
   A test: the Director's prompt of F1 and F3 holds it, a trial's does not.
11. AN ACT'S FIRST PICTURE IS A GUARANTEE, NOT A SHARE OF WHAT IS LEFT. `firsts` taken "`[:left]` ... never beyond the budget" means: when the opening
   shots have used the budget (`left` is `d["stills"]` after `_apply_tier`, and the opening is taken first), an act's first still gets no picture,
   `camera_path` rule 2 fails, and the video is held before a rupee is spent for want of a still of under Rs 1 - a hold no rewrite repairs.
   `anchor_shots` already knows two such guarantees ("whatever the budget says": the first still, the first still after the footage) and a
   repetition guard that adds up to twelve. The memo must make `firsts` one of them, say the worst case in 3.8 honestly (at most one still an
   act: under Rs 15 a video at the allowance of 13 changes; usually none), give `anchors_for` its real arguments (the units are not in `S_`), and
   say what happens when an act's first picture fails twice to be made (today up to 15% of the pictures may fail and the film goes on).
12. THE SHORT'S HOOK IS NOT ON THE LADDER ROW. `ladder.enter` writes `"hook": rec.get("hook")` and `shorts2` fills it with `arch` - the NAME of the
   hook archetype ("you_pov", "countdown"). The spoken line lives only in the footage archive (`opening.fetch` -> `man["hook"]`), which is fetched in
   the plan stage AFTER the room, and the draw's ladder id is set after the room too. Typed as written ("whose hook the ladder row holds ... the
   builder names the reader") the writer is told: begin "with exactly this line, word for word: \"you_pov\"". The memo must say where the room
   gets the spoken line (the archive fetched before the room for the pitch `ladder.pitch()` returns, or the line kept on the row from now on with
   the older rows falling back to today's insert) and demand a test that builds the ladder row the way `shorts2` / `ladder.enter` really do.
13. THE OTHER PLACES THAT STILL DEMAND AN ASK, THE EMOTION BEAT AND A SECOND VOICE. "The asks are demanded by the writer's base prompt" is half the
   truth. Found by search, each needs a line in the memo: (a) `engage.brief` (in every writer's brief through `_writer_extra`): "AUDIENCE PROMPTS:
   use at most two ... comment, predict, take a side or share with a friend" - beside F3's "NO ASK" and F1's "no share ask"; and "EMOTION BEAT ...
   in act 3 or just before the verdict" - a courtroom word in an F1 / F3 brief, and the emotion beat is a scope line of issue 74 that the memo
   neither builds nor decides (a scope line is never dropped silently: the plan's chapter 12); (b) `prompts.FACTFIX` and `room.oc_rewrite` tell the
   rewriter to keep "the three audience asks"; (c) `format_engine.check_script` (`FORMAT_GATE_ON`): in F3 "one role barely speaks (DIRECTOR n,
   SKEPTIC 0)" is true of EVERY script, so `room.format_pass` pays for a fix that asks the writer to "make the Curious One question assumptions"
   - at both of its call sites - and `FE.instructions` tells the writer, the bible and the critic about "the two roles"; `prompts.WRITER` says
   "Banter style between the two roles". The memo must list every such place (search "SKEPTIC", "Curious One", "two roles", "three audience
   asks", "verdict") and say for each what F1 and F3 get; at the least `check_script` asks the format's row for its voices, with a test that an
   F3 production makes no paid `format` call for a missing second role. Open issue 187 is not an answer to a paid call that fights the format.
14. THE VOICE MEASURE: ONE SPEAKER PARSER, AND THE TRUE FIGURES. (a) "`speaker` = the label of the line" is a second parser: `voice._peel` and
   `parse_script` know the aliases ("[THE CURIOUS ONE]", "**Skeptic:**"), a label alone on its line that belongs to the next line, and two speakers
   on one line. A foil line under "[CURIOUS ONE]" would count as the guide's, its "I" would not count, and a good F1 script could fall under its
   floor for its label style. `inside.sentences` must take its speakers from `voice`'s parser. (b) The four passages must be given line by line
   (GOOD-1 is printed as one paragraph with five labels in it: as ONE line every sentence is the first label's). (c) The hand counts are wrong -
   measured with `layman._SENT` / `_TOK` and the memo's `YOU` / `ME`: "The ceiling arrives slowly." has FOUR words and is counted (outside);
   GOOD-1 = 10 of 11 = 90.9%, longest run from outside 1; GOOD-2 = 10 of 15 = 66.7%, run 4 (it clears the memo's own bar of 65 by 1.7 points,
   not by 6.4); GOOD-2 with the fifth sentence = 10 of 16 = 62.5%, run 5 - fails (b) alone, as said; BAD-1 = 0 of 8, run 8. The memo must carry
   these figures. (d) Rule (c) must say what an act with NO inside sentence at all is (BAD-1 is one: its "because" sentence comes before a first
   inside sentence that never comes) - it fails, said in words; and "fewer than 8 counted sentences is not judged" must say that 8 is judged.
15. F2'S LIMITS HAVE NO GOOD PAIR. Question 5 of the review: both kinds of measured pairs before a limit. For a trial there is one bad figure (the
   offline trial: 26%, a run of 8) and no good one - all four passages are a guide and a foil. The floor 30 lies UNDER the 40 the memo calls bad
   (the offline F1 script, 33 to 35%, would pass it), and "at most 4 sentences in a row from outside" is the same number for one guide's voice and for
   a courtroom of four voices in which a character's "I" never counts. The memo must add a GOOD trial passage written by the designer (a judge, a
   witness, the two leads; measured under F2's rule, its share and its longest run written down), set F2's floor and run limit between that and
   the bad one - a `LECTURE_MAX_SENTENCES` per format if the numbers ask for it - and widen open issue 185 to F2.
16. THE ORDER OF 3.9 AND THE GAPS A TYPIST CANNOT FILL. (a) Step 1 "no behaviour changes yet; the whole older suite is green" cannot be green:
   `truth.unread_settings` refuses a cell no code names (`LECTURE_MAX_SENTENCES`, `ACT_MIN_S`, `PLACE_CHANGES_PER_MIN_MAX`, `ENDING_FREE_S`,
   `V12V2B_MOVE_DONE`, the four switches) and the wiring test refuses the four readers nobody calls yet; the lists may only shrink. Each cell,
   switch, reader and lever must land in the step that first uses it. (b) `p_living`'s chip rule is judged only when `CHIP_DRAWN_ONLY_ON` is TRUE.
   (c) `inside.open_acts` re-uses `audience.shape`'s INNER helper `still`: say that it is lifted to a module function of the PROTECTED file. (d)
   `open_acts` works on the script's beats, `path.acts` on the joined acts: say so. (e) The allowance join: "the SHORTEST remaining act joins the act
   before it" - and when the shortest is the first? (f) A timeline saved before this batch has no `beat` on any unit: both checks NA, not one act
   for the whole film. (g) `teased_pitch` must keep reading the cell: it honours what the video BEFORE promised, whatever the format of this one.
   (h) `path.lay` and the marks: it skips `short`; say in words what it does to a `promise` shot (its prompt is the thumbnail's scene, which may
   be another place) and to an `anim` shot (`anim.start_frame` builds its own start picture), and list by search every step after `lay` that
   reads or rebuilds a prompt.

## The seven attacks asked for beyond the ten questions
(a) Exact enough to type? The arithmetic of 3.2 holds (82 s: max(3, floor(2.05)) = 3, nothing joins; 9 min, 20 headings: 19 changes, allowed 13, six
    join). The passages do not give the stated figures (change 14). Not typeable as written: 1, 2, 5, 8 (where the fields travel), 9 (the pools), 12, 16.
(b) False about today's code: the beat in `voice.py` (1); "the ladder row holds" the hook (12); "outside the tail" for the check's window (5); "the
    nearest earlier picture ... is a picture of that act" (3); "the asks are demanded by the writer's base prompt" as the only place (13); "has three
    words" (14). TRUE as checked: every count of the experiment that code can show without a run - the rotation of angle in `assign_anchors`, `sgn =
    rng.choice`, `pull` and `kb_roll` in the calm pool, `img = own or prev_img`, the three call sites of `CTA.ensure`, `tease_brief` / `ensure_tease`,
    the chip names.
(c) A good video held for a reason the rule does not recognise: 3, 4, 5, 6, 7, 11, 13 (F3), 15. A bad one passed: 1, 2, 9, 10 - and the two the
    memo names itself (a "you" in every sentence; a place that is only a sentence).
(d) Marks: `open_acts` skips `short`, `promise`, `anim` (right); `lay` skips `short` only and rewrites the prompt of `promise` and `anim` shots
    (16 h); `motion.place` treats an act's first still as plain room for a clip (3); a living shot's `buy` is not touched (right).
(e) The order of 3.9: not green after step 1 (16 a); steps 2 to 9 are in dependency order once 1 and 16 are settled.
(f) What a viewer gets, in his words: a voice that talks to HIM, now, and never lectures for more than a few sentences; every picture from where
    he stands instead of five camera heights; a camera that never backs away or tilts and drifts one way through a scene; no picture left over from
    the scene before; one ask in the middle instead of three and a promise of a video that may never be made; the film ends on a question to him;
    no name tag for people he never sees; one video in five is a walk with one voice. What is only machinery until the pilot: "one place" (a
    sentence in a prompt), the walk as a format a real writer has never written, every floor. What he does NOT get, said plainly: the "continuous
    camera" of item 19 - stills cannot do it and nine animated minutes cost four times the budget (the redesign's 10.7).
(g) The worst video: question 9.

## What is sound and should not move
The choice of D and the case built against it; the format row as the one place that decides (four keys, four switches, off = d8101c8); the voice
measured as share, run and "shows before it explains", with the past tense recognised only where code can recognise it and the error given to the
writer; eye level at the source instead of asked of a model; the render record judged, not the plan; no tease the ladder cannot keep (issue 101
decided); a name only for a character who is drawn; one subscribe ask in F1 and none in F3 as the first comparison (H29); nothing new paid; the
honesty of "CHANGED FROM THE REDESIGN", "NOT IN THIS BATCH" and open issues 185 to 190.
