"""whatifs/data.py v8.7 - seed data loaded into the Sheet at setup: topic grids, banned list, strategy pools, director lessons."""
import hashlib, itertools, random

EVERYDAY = ["nail clippings","sneezes","blinks","yawns","hiccups","footsteps","toilet flushes","hair strands","tears","burps",
 "cups of coffee","phone screens","microwaves","fridge doors","car horns","light switches","shower drips","pieces of chewing gum","pencils","paper cuts",
 "eyelashes","fingerprints","heartbeats","shadows","snores","hand claps","whistles","jumps","high-fives","sighs",
 "grains of rice","ice cubes","balloons","sugar cubes","pillows","shoelaces","coins","toothbrushes","sunglasses","umbrellas"]
COLLECTIVE = ["all 8 billion people dropped their {x} into the ocean at the same second","every {x} on Earth happened at exactly the same moment",
 "every {x} on Earth vanished overnight","nobody on Earth made a single one of their {x} for a day","everyone's {x} were collected into one pile",
 "every {x} ever made came back at once","all {x} on Earth doubled in size","every one of the {x} on Earth became magnetic",
 "all {x} on Earth fell upward for ten seconds","all {x} on Earth turned to solid gold","all {x} became as heavy as a car",
 "all {x} on Earth were launched into space","all {x} on Earth glowed in the dark","all {x} made a sound you could hear from orbit",
 "you could only have ten more {x} in your life","all {x} on Earth were teleported to the Moon","all {x} on Earth froze to absolute zero",
 "all {x} became self-aware for one minute","all {x} on Earth were dropped from the edge of space","all {x} on Earth started orbiting your head",
 "everyone made their {x} in perfect sync every second","all {x} on Earth were a thousand degrees hot","all {x} on Earth turned into antimatter",
 "all {x} in history were stacked into one tower","all {x} on Earth started shrinking forever","every one of the {x} was replaced by a tiny black hole",
 "all {x} on Earth became edible","all {x} on Earth popped like firecrackers","your {x} kept multiplying and never stopped","all {x} on Earth arrived at your house"]
STRANGE = ["your skin bacteria","the dust on the Moon","the air in your lungs","the iron in your blood","the water in your body","your stomach acid",
 "the Sun's light","Earth's magnetic field","the Mariana Trench","Saturn's rings","a teaspoon of neutron star","deep-ocean pressure",
 "a single atom","the speed of sound","your nerve signals","your bones","the ozone layer","clouds","a mosquito","an ant colony"]
RULES = ["became 1,000 times stronger","switched off for 60 seconds","could be touched","were the size of a city","landed in your living room",
 "followed you everywhere","worked backwards","became visible","could talk","sped up 100 times",
 "were sold at the supermarket","became your only food","became a national border","turned into honey","got a mind of its own",
 "fit in your pocket","lasted forever","appeared for one second a day","doubled every hour","could be heard"]
BANNED = [("earth stopped spinning","overused"),("earth stops spinning","overused"),("oxygen disappear","overused"),("speed of light meteor","overused"),
 ("meteor at the speed of light","overused"),("asteroid at the speed of light","overused"),("hits jupiter","lame"),("moon disappear","overused"),
 ("sun disappear","overused"),("fell into a black hole","overused"),("gravity disappear","overused"),("earth was flat","overused"),
 ("dinosaurs never","overused"),("sun exploded","overused"),("earth stopped for","overused"),
 ("cure for","policy: medical"),("you should take","policy: advice"),("election","policy: politics"),("president","policy: real person"),("terror","policy: real events")]

def ptype_for(text):
    t = text.lower()
    if any(k in t for k in ["moon","sun","saturn","neutron","space","orbit","black hole","antimatter","magnetic field","ozone"]): return "cosmic"
    if any(k in t for k in ["skin","blood","bones","lungs","stomach","nerve","heart","teeth","body","tears","eyelash","hair","sneez","yawn","hiccup","burp","snore","blink"]): return "body"
    return "collective"

STRATEGIES = {
 "story": {"S1_escalation": "Ordinary moment, then each beat raises scale or stakes; end on the biggest consequence and one human-sized image.",
  "S2_climax_first": "Open on the climax (6-12 s), freeze, ask 'how did we get here?', rewind to the ordinary start, build back, replay the climax with new meaning, then a twist.",
  "S3_countdown": "Clock structure: second 1, minute 1, hour 1, day 1, year 1. Time on screen each beat.",
  "S4_two_timelines": "Two timelines cut together (you in your kitchen / the planet). They collide at the climax.",
  "S5_false_ending": "Apparent resolution at ~70%, viewer relaxes, then the overlooked consequence turns out bigger.",
  "S6_question_chain": "Each answer opens a stranger question. 5-7 linked questions. Final answer loops to the first.",
  "S7_reverse": "Start with the final state of the world, then go back step by step to the tiny cause."},
 "hook": {"O1_second_person": "Put the viewer inside it in the first sentence.", "O2_number_shock": "One specific absurd number in the first 5 seconds.",
  "O3_cold_climax": "Most spectacular frame, no context, one line.", "O4_wrong_assumption": "'You think nothing would happen. You'd be wrong.'",
  "O5_sound_first": "A strange sound in black, then reveal what made it.", "O6_tiny_detail": "Extreme close-up of something ordinary, pull back to reveal scale.",
  "O7_deadline": "A countdown on screen in the first 3 seconds.", "O8_dry_joke": "Deadpan relatable aside, then hard cut to dread."},
 "voice": {"hypnotic": "Slow, low, long pauses.", "urgent": "Faster, short gaps.", "slow_burn": "Starts calm, speeds up.",
  "brake": "Starts fast, slows for the reveal.", "conversational": "Like telling a friend."},
 "reel": {"R1_climax_why": "Climax first, then 'but why?'. Cut to black on the question.", "R2_countdown": "'Second 1... second 10...' stop one step before the answer.",
  "R3_myth": "'Most people think X. They're wrong.' Cut before the answer.", "R4_three_facts": "Three facts, the third held back.",
  "R5_scale_ladder": "Body, then city, then planet. Freeze at planet level."},
 "humour": {"none": "No jokes.", "light": "One dry aside in the cold open and one end callback.", "medium": "Cold-open aside, relief line after the peak, end callback (max 3)."},
 "thumb": {"T1_object_scale": "One ordinary object, enormous, against a dramatic landscape.", "T2_before_after": "Split frame: normal world vs aftermath.",
  "T3_silhouette": "Silhouetted person, rim-lit, facing the impossible scene. No real person.", "T4_number": "One giant number + one tiny object.",
  "T5_question": "Short question in huge type over the climax frame.", "T6_macro": "Extreme macro of something familiar, gone wrong."},
 "title": {"N1_what_if": "What If [specific absurd premise]?", "N2_you": "What If You [did X] for [time]?", "N3_number": "What If 8 Billion People [did X] At Once?",
  "N4_happens": "What Actually Happens If [X]", "N5_wrong": "Everyone Is Wrong About What Happens If [X]"},
}
# ---------------- v7.1: 12 topic families (rotated, learned, 'everyone on Earth' capped) ----------------
FAMILIES = {
 "F01_body": ("Your body", "body", ["your bones","your skin","your blood","your heart","your lungs","your teeth","your eyes","your brain","your stomach","your hair"],
   ["What if {x} turned to glass for 24 hours?","What if {x} became completely see-through?","What if {x} worked twice as fast forever?","What if {x} stopped for exactly ten seconds?",
    "What if {x} glowed every time you lied?","What if {x} grew back brand new every night?","What if {x} were swapped with a stranger's while you slept?","What if {x} ran on sunlight?",
    "What if {x} aged 50 years in one day?","What if {x} could talk back?"]),
 "F02_time": ("Time", "collective", ["one second","your sleep","every Monday","your childhood","the last hour","midnight","your lunch break","sunrise","your future","yesterday"],
   ["What if {x} lasted a full year?","What if you could rewind {x} only once?","What if {x} was erased from everyone's memory?","What if {x} moved ten times slower for you only?",
    "What if you could sell {x}?","What if {x} repeated until you fixed one thing?","What if {x} came with a countdown only you could see?","What if {x} could be stolen?",
    "What if {x} skipped ahead without warning?","What if {x} happened twice in a row?"]),
 "F03_scale": ("Scale", "collective", ["a grain of sand","a single ant","a raindrop","a drop of honey","a snowflake","a mosquito","a coin","a strand of hair","one cell of your body","a teaspoon of water"],
   ["What if {x} weighed as much as a mountain?","What if {x} were the size of New York?","What if {x} were a million degrees hot?","What if {x} moved as fast as a bullet?",
    "What if {x} landed on your tongue at the size of a bus?","What if {x} were dropped from the edge of space?","What if {x} could never be destroyed?","What if {x} became a black hole?",
    "What if {x} doubled every minute?","What if {x} were made of neutron star matter?"]),
 "F04_senses": ("Senses", "body", ["Wi-Fi signals","sound","heat","smells","gravity","ultraviolet light","radio waves","your own heartbeat","magnetic fields","electricity"],
   ["What if you could see {x}?","What if you could taste {x}?","What if you heard {x} all the time?","What if {x} suddenly became painful?","What if you lost the ability to feel {x}?",
    "What if {x} had a colour?","What if {x} were ten times stronger?","What if {x} could be recorded and replayed?","What if only you could sense {x}?","What if {x} switched off for an hour?"]),
 "F05_tech": ("Everyday tech", "collective", ["your phone","the internet","GPS","your earbuds","elevators","traffic lights","the cloud","your smartwatch","satellites","the power grid"],
   ["What if {x} went offline forever at noon?","What if {x} had a million times more power?","What if {x} could read your thoughts?","What if {x} started lying to you?",
    "What if {x} had never been invented?","What if {x} became alive for one hour?","What if {x} only worked when you were happy?","What if {x} leaked everything it ever recorded?",
    "What if {x} became 100 times faster overnight?","What if {x} chose who it worked for?"]),
 "F06_nature": ("Nature", "cosmic", ["trees","the ocean","clouds","rain","volcanoes","rivers","the wind","lightning","coral reefs","mushrooms"],
   ["What if {x} screamed when hurt?","What if {x} could move on their own?","What if {x} stopped for one week?","What if {x} were 1,000 times bigger?","What if {x} turned to glass?",
    "What if {x} became intelligent?","What if {x} appeared in your bedroom?","What if {x} ran backwards?","What if {x} glowed at night?","What if {x} vanished from Earth?"]),
 "F07_places": ("Extreme places", "cosmic", ["the Mariana Trench","Mount Everest","the Sahara","Antarctica","the far side of the Moon","the Amazon","the inside of a volcano","the bottom of Niagara Falls","the edge of space","a hurricane's eye"],
   ["What if you rode a glass elevator to {x}?","What if you had to live in {x} for 30 days?","What if your house were teleported to {x}?","What if {x} were moved next to your city?",
    "What if you woke up in {x}?","What if {x} were your daily commute?","What if you shouted in {x}?","What if you lit a match in {x}?","What if you spent one minute unprotected in {x}?",
    "What if you dropped your phone in {x}?"]),
 "F08_rules": ("Strange rules", "collective", ["colour","friction","shadows","echoes","sleep","reflections","lying","forgetting","gravity","silence"],
   ["What if {x} disappeared for 24 hours?","What if {x} were illegal?","What if {x} cost money?","What if {x} worked backwards?","What if {x} only existed at night?",
    "What if {x} doubled every day?","What if {x} could be bought and sold?","What if {x} happened only to you?","What if {x} switched off for one second?","What if {x} were invented tomorrow?"]),
 "F09_space": ("Space, up close", "cosmic", ["Saturn's rings","the Sun","a comet","the Moon","Mars","a black hole","the International Space Station","Jupiter's Great Red Spot","a neutron star","Venus"],
   ["What if you took a bath in {x}?","What if {x} were in your backyard?","What if you touched {x} for one second?","What if {x} made a sound we could hear?","What if {x} were the size of a car?",
    "What if you swapped places with {x} for a day?","What if {x} showed up in tonight's sky?","What if {x} followed Earth like a pet?","What if {x} were for sale?","What if {x} were made of candy?"]),
 "F10_food": ("Food and chemistry", "body", ["chewing gum","coffee","chili peppers","salt","sugar","honey","popcorn","ice cream","bread","tap water"],
   ["What if you chewed {x} for 30 days straight?","What if {x} were the only thing you could eat?","What if {x} were a million times stronger?","What if {x} exploded when heated?",
    "What if {x} disappeared from Earth?","What if your body made {x}?","What if {x} cost more than gold?","What if {x} froze instantly in your mouth?","What if a lake were made of {x}?",
    "What if {x} became addictive overnight?"]),
 "F11_future": ("Future tech", "collective", ["your memories","your face","your voice","your dreams","your DNA","your heartbeat","your thoughts","your shadow","your personality","your sleep"],
   ["What if {x} were backed up to the cloud and hacked?","What if {x} could be rented out?","What if {x} were copied by a stranger?","What if {x} could be edited like a photo?",
    "What if {x} were sold at auction?","What if {x} were streamed live?","What if {x} were deleted by mistake?","What if {x} needed a monthly subscription?","What if {x} were owned by a company?",
    "What if {x} got an update you didn't want?"]),
 "F12_everyone": ("Everyone on Earth", "collective", EVERYDAY[:12], [("What if " + c + "?") for c in COLLECTIVE[:10]]),
}
FAMILY_PTYPE = {k: v[1] for k, v in FAMILIES.items()}
FAMILY_PLAYLIST = {k: "What If: " + v[0] for k, v in FAMILIES.items()}
STRATEGIES["family"] = {k: v[0] for k, v in FAMILIES.items()}
# v8.2: how the two roles play off each other. Each is a learnable strategy (scored on retention like every other dimension).
STRATEGIES["banter"] = {
 "B1_patient_expert": "The Director keeps asking the Curious One to wait ('hold on, watch this part'); the Curious One bursts out only when the payoff actually lands.",
 "B2_doubter_proven_wrong": "The Curious One doubts a claim out loud ('no way that happens'); the picture proves the Director right and the Curious One reacts honestly to being wrong.",
 "B3_shared_dread": "Both go quiet at the peak; one short, human line from the Curious One ('...oh no') instead of a shout; humour only in the relief afterwards.",
 "B4_running_gag": "One small recurring joke the Curious One keeps returning to (one object, one worry); it pays off at the end. Never more than three mentions.",
}
STRATEGIES["title"]["N6_statement"] = "Statement + consequence, no question mark: 'Your Bones Are Glass Now. Don't Sneeze.'"

# ---------------- v8.7: rhythm blueprints + sensory density (learned strategies), cold-open devices and pattern interrupts (rotated, least recently used) ----------------
STRATEGIES["rhythm"] = {
 "RB1_slow_fuse": "Quiet, intimate cold open (one [close] line, near-silence), then every beat raises the stakes one notch; the interrupt lands in the middle third; reactions held back until the peak.",
 "RB2_double_peak": "A false climax at about 55% (relief, one dry joke), then the real and bigger consequence at about 80%; reactions cluster after each peak.",
 "RB3_pressure_cooker": "Short sentences, fast cuts, a clock or counter on screen from the first seconds, hard silence before every reveal; reactions short and frequent.",
 "RB4_breathing_room": "Fast escalation broken once, after the midpoint, by a 10-15 s held breath (picture + one sound texture, almost no words) before the final climb.",
 "RB5_case_file": "Built like an investigation: clue, test, result; every test ends on a new question the Curious One asks; the answer to the first question arrives last.",
 "RB6_end_first": "Open on the final state of the world for 10 s, then rewind to the tiny cause and climb back; time stamps mark each section; one big reaction at the very end.",
}
RHYTHM_SPECS = {"RB1_slow_fuse": {"arc": "build", "reactions": "sparse"}, "RB2_double_peak": {"arc": "waves", "reactions": "medium"},
                "RB3_pressure_cooker": {"arc": "pulse", "reactions": "dense"}, "RB4_breathing_room": {"arc": "still", "reactions": "sparse"},
                "RB5_case_file": {"arc": "waves", "reactions": "medium"}, "RB6_end_first": {"arc": "build", "reactions": "sparse"}}
STRATEGIES["sound"] = {"SD_sparse": "Few textures (about 1 shot in 10): sound only where it carries the story; silence does the rest.",
                       "SD_textured": "About 1 shot in 5 carries a close texture that matches the picture.",
                       "SD_rich": "About 1 shot in 3 carries a texture; the world feels physical and close (still never under a reaction or two in a row)."}
OPENERS = {"image_first": "Open on the impossible image in near-silence; the first words come only after the viewer has SEEN it.",
           "mid_action": "Start in the middle of the event already happening, then say how we got here.",
           "wrong_guess": "The Curious One confidently guesses what happens; the Director says 'no' and shows the first proof.",
           "sound_first": "A strange, close sound before any word; then reveal what made it.",
           "number_drop": "One specific, absurd number in the first sentence, then what it means for you.",
           "you_now": "Second person, present tense: it is happening to you, right now, where you are sitting."}
INTERRUPTS = {"freeze_frame": "'Pause the simulation': the Director freezes the moment to point at one detail nobody noticed.",
              "rewind": "Replay a moment just shown, from a new angle or scale, and reveal what it really meant.",
              "scale_jump": "A sudden cut from one human-sized detail to the whole planet (or the reverse).",
              "fake_out": "A false resolution: it looks solved, then the overlooked consequence arrives.",
              "quiet_beat": "Five to eight seconds with almost no words: one picture, one close sound, then the turn.",
              "guess_first": "The Curious One asks the viewer to guess before the answer; the answer lands 20-30 s later.",
              "two_places": "Cut between two places at the same second (your kitchen / the other side of the world) until they collide.",
              "speed_run": "Ten seconds that compress an hour into a rapid run of numbers and pictures, then a hard stop."}
# v8.7 Playbook seed: research-graded rules (department, metric they should move, source, evidence). Code, not the model, sets evidence labels for new rules.
PLAYBOOK_SEED = [
 {"department": "writer", "metric": "open", "evidence": "official", "source": "https://support.google.com/youtube/answer/9314415",
  "rule": "The first 30 seconds must visibly deliver what the title and thumbnail promised; YouTube's Intro report is the share still watching at 30 s."},
 {"department": "packager", "metric": "pack", "evidence": "official", "source": "https://support.google.com/youtube/answer/16391400",
  "rule": "Judge a title and thumbnail by the watch time they earn per impression, not clicks alone; a package that wins clicks but loses viewers is worse."},
 {"department": "showrunner", "metric": "hold", "evidence": "official", "source": "https://support.google.com/youtube/answer/1311392",
  "rule": "Every episode must differ in structure, opening device and pacing, not just topic; templated, mass-produced videos are not eligible for monetization.",
  "note": "YouTube channel monetization policies, 'Inauthentic content' section (renamed July 2025; applies to the whole channel)"},
 {"department": "writer", "metric": "hold", "evidence": "plausible", "source": "https://feeds.simonwillison.net/2024/Sep/15/how-to-succeed-in-mrbeast-production/",
  "rule": "Minute one proves the thumbnail, minutes one to three show instead of tell, re-engage around 3:00 and again around 6:00."},
 {"department": "writer", "metric": "hold", "evidence": "plausible", "source": "https://ppc.land/subscribers-skip-90-of-uploads-in-their-feed-youtube-director-says/",
  "rule": "Never make the viewer wait for a payoff that does not come; YouTube weighs satisfaction, so every question you open must be answered.",
  "note": "secondary report of a Creator Insider interview (Sept 2026)"},
 {"department": "packager", "metric": "pack", "evidence": "plausible", "source": "https://ytgrowth.io/blog/youtube-title-length",
  "rule": "Title length alone does not predict views in recent studies; keep titles short enough not to be cut on phones and put the key words first."},
 {"department": "director", "metric": "hold", "evidence": "plausible", "source": "https://kurzgesagt.org/youtube/",
  "rule": "Give every video its own sound: a score and effects built for it change how it feels; keep textures low under the voice."},
]

AI_TELLS = ["delve", "tapestry", "in this video", "let's dive", "dive in", "buckle up", "imagine a world", "fascinating", "it's important to note",
            "in conclusion", "embark", "journey", "unleash", "realm", "testament to", "intricate", "moreover", "furthermore", "whether you're",
            "stay tuned", "mind-blowing", "game-changer", "here's the thing", "let that sink in", "ever wondered", "in today's", "plethora", "navigate the"]

def premise_rows():
    rows = []
    for fam, (label, ptype, anchors, templates) in FAMILIES.items():
        for x, t in itertools.product(anchors, templates):
            p = t.format(x=x) if "{x}" in t else t
            rows.append({"premise_id": fam[:3] + hashlib.md5(p.encode()).hexdigest()[:7].upper(), "grid": fam, "anchor": x, "rule": t[:60],
                         "lens": label, "premise": p, "ptype": ptype, "status": "FRESH", "episode_id": "", "used_at": ""})
    seen, out = set(), []
    for r in rows:
        if r["premise"] not in seen: seen.add(r["premise"]); out.append(r)
    random.Random(7).shuffle(out); return out

def strategy_rows():
    return [{"dimension": d, "name": n, "definition": t, "status": "ACTIVE", "plays": 0, "score_sum": 0, "score_n": 0, "created": "seed", "source": "seed"}
            for d, items in STRATEGIES.items() for n, t in items.items()]

DIRECTORS = """Craft lessons (learn the technique, never copy a scene):
Hitchcock - show the bomb under the table before the character knows. Nolan - converging timelines, ticking clock.
Villeneuve - scale through silence; tiny human vs vast structure. Spielberg - show the effect before the monster (the water ripple).
Fincher - precise unsettling detail. Kubrick - symmetry, slow push-ins. Cuaron - long unbroken dread.
Bong Joon-ho - dry laugh then sudden horror. Edgar Wright - cuts on sound, visual punchlines, callbacks. Jordan Peele - comedy timing used for fear.
Rod Serling - ordinary premise, ironic last turn. Sagan/Attenborough - one intimate human sentence after the huge number.
Kurzgesagt/Vsauce - every answer opens a better question. MrBeast packaging - title and thumbnail promise one clear impossible image."""

# ---------------- v8.0: craft reminders per department (technique names only; nothing here quotes or copies any work) ----------------
CRAFT = {
 "retention": ("Retention rules (v8.7 minute map; YouTube's 'Intro' report = share still watching at 30 s, high when the opening matches the title and thumbnail; "
               "the 'How to Succeed in MrBeast Production' guide): 0:00-0:30 prove the promise, the thumbnail's image on screen and the stakes said plainly, no "
               "throat-clearing; 0:30-3:00 show, don't tell, and escalate fast; around 3:00 a re-engagement that genuinely impresses; 3:00-6:00 the most exciting "
               "simple consequences; around 6:00 a second re-engagement; a re-hook (a new question, a number, a turn) at least every 60-90 s; never make the viewer "
               "wait for a payoff that never lands (YouTube counts satisfaction, not just minutes): every question you open gets answered; the biggest consequence "
               "and one human-sized image in the last minute, before the share ask."),
 "writer": ("Vonnegut's story shapes (for example 'man in a hole': trouble, a climb out, then a bigger fall): pick one shape and keep it. "
            "Pixar story spine ('once upon a time... every day... until one day... because of that... because of that... until finally') for the cause-and-effect chain. "
            "'But / therefore' rule (Parker and Stone): link beats with 'but' or 'therefore', never 'and then'. "
            "Ira Glass: alternate anecdote (what happens) with reflection (why it matters) and raise a question early that the story answers later. "
            "Chekhov: plant every object early that pays off later."),
 "psychologist": ("Loewenstein's information-gap theory: curiosity peaks when people know a little and sense a specific gap, so never give the whole picture early. "
                  "Zeigarnik effect: unfinished loops stay in mind; open one, keep it open, close it later and say so. "
                  "Peak-end rule (Kahneman, Fredrickson): viewers remember the peak and the ending, so make both count. "
                  "Excitation transfer (Zillmann): dread followed by relief makes the relief and the humour land harder. "
                  "Benign-violation theory (McGraw, Warren): humour works when something is wrong but safe; never joke when it is not safe. "
                  "Self-reference effect: facts tied to the viewer ('your kitchen') are remembered better. "
                  "Berlyne: novelty and surprise hold attention; too much complexity loses it."),
 "director": ("Use the director lessons above. Also: one clear visual idea per shot; keep one recurring object or colour as a motif; "
              "hold on silence at the peak instead of adding motion; never show the monster before the effect. "
              "v8.7 sound: give a few shots ONE close, quiet texture from the fixed palette (drip, crackle, wind, heartbeat, hum, fizz, rumble, tick, rain, glass) that "
              "matches what is on screen; the music drops out just before each peak by itself."),
 "editor": ("Walter Murch's rule of six for a cut, in order of importance: emotion, story, rhythm, eye-trace, two-dimensional screen space, three-dimensional space. Cut for emotion first. "
            "J-cuts and L-cuts: let sound lead or trail the picture across a cut. "
            "Sound before picture: a sound heard before the image appears creates dread. "
            "Silence is a sound: drop the bed just before the peak so the peak hits. "
            "Vary shot length: a long hold after a fast run reads as weight. "
            "v8.7 (built into the mixer): every episode has its own music arc and section changes, near-silence before each peak, a hush under [close] lines, "
            "and code-made textures (drip, crackle, wind, heartbeat...) under the shots that show them; plan the beats so these moments exist."),
 "packager": ("Curiosity gap (Loewenstein): the title asks a question the thumbnail does not answer. "
              "Title and thumbnail promise ONE impossible image and the video must deliver it. "
              "Specific beats vague: a number, an object, a time. "
              "Test the thumbnail at phone size and with the title covered. "
              "Start from the viewer's wrong intuition and promise to test it. Never promise what the script does not show. "
              "v8.6 click rules (YouTube creator guidance, the 'How to Succeed in MrBeast Production' guide, large title studies): decide title + thumbnail as ONE promise "
              "that the first minute visibly pays off; titles 30-60 characters with the strongest words in the first half (phones cut the end); at most one ALL-CAPS word; "
              "thumbnail text 1-4 words that ADD to the title, never repeat it; one focal subject, big and high-contrast, readable at phone size; keep the bottom-right "
              "corner empty (YouTube's timestamp covers it); no clickbait the video does not deliver (it is punished by retention)."),
 "reel": ("Open on the strongest frame in the first second; one idea per reel; cut for emotion (Murch); motion or a change of picture every 1-2 seconds; "
          "follow the reel style in the brief (v8.5 default 'bridge': give one real payoff, leave the episode's bigger question open, invite to the full video)."),
}
CRAFT["writer"] = CRAFT["retention"] + " " + CRAFT["writer"]          # v8.6: the memos and the humanize pass carry the retention rules too
CRAFT["humanize"] = CRAFT["writer"] + " " + CRAFT["psychologist"]
CRAFT_BY_ROLE = {"WRITER": CRAFT["writer"], "AUDIENCE PSYCHOLOGIST": CRAFT["psychologist"], "DIRECTOR + DP": CRAFT["director"],
                 "EDITOR + SOUND": CRAFT["editor"], "PACKAGER": CRAFT["packager"], "REEL PRODUCER": CRAFT["reel"]}


# ---------------- v8.9: locked visual style, living-still atmosphere, rotating guest voices ----------------
# The style is a Settings cell (STYLE_LOCK) so it can be tuned without code; this is its default. Thumbnails/covers get THUMB_STYLE instead:
# the dark look is kept but the subject stays brightly lit, because a dark thumbnail is unreadable on a phone (CTR first).
STYLE_LOCK = ("cinematic dark atmosphere, volumetric lighting, god rays, deep shadows, high contrast, subtle film grain, epic scale, "
              "the main subject clearly lit and readable")
THUMB_STYLE = "volumetric god rays, epic scale, dark cinematic background, the focal subject brightly lit and sharp"
# Living stills (image-to-video): atmosphere that moves. Chosen from what the shot shows; the opening window gets the strongest wording.
ATMOS = ((r"fire|lava|volcan|burn|flame|spark", "embers and heat shimmer rising, flickering firelight"),
         (r"water|ocean|sea|lake|river|rain|wave|ice|frozen", "water rippling and catching the light, mist drifting low"),
         (r"space|orbit|star|planet|moon|sun|galaxy|black hole", "slow cosmic dust drifting through god rays, distant light pulsing"),
         (r"city|street|building|road|car|room|house|kitchen", "volumetric haze drifting through light beams, dust motes floating, distant lights flickering"),
         (r"storm|wind|cloud|sky|air|desert|dust", "clouds racing, wind-blown dust and haze sweeping across the frame"))
ATMOS_DEFAULT = "volumetric fog drifting slowly through god rays, fine particles floating, light subtly shifting"
LIVING_MOTION = {"opening": "noticeable slow dolly push toward the subject, strong atmospheric motion, dramatic and alive",
                 "calm": "slow gentle camera drift, atmospheric motion, steady and cinematic"}
# Rotating guests for the Curious One (the [SKEPTIC] role): a different, clear voice and a different everyday persona each episode, so the show feels
# like the Director interviewing a new guest. Clarity first: Kokoro's highest-graded voices (VOICES.md: af_heart A, af_bella A-, af_nicole and bf_emma B-,
# am_puck C+), each a single dominant voice (blending three voices smears the timbre). Personas are invented everyday people, always adults, never real.
GUESTS = {
 "G1": ("the night-shift nurse who has seen everything", {"af_heart": 1.0}),
 "G2": ("the bridge engineer who trusts numbers, not stories", {"bf_emma": 0.85, "af_bella": 0.15}),
 "G3": ("the amateur astronomer with a dry sense of humour", {"am_puck": 0.85, "am_michael": 0.15}),
 "G4": ("the first-year med student who asks the obvious question", {"af_bella": 0.9, "af_heart": 0.1}),
 "G5": ("the soft-spoken librarian who notices tiny details", {"af_nicole": 0.85, "af_heart": 0.15}),
}

# =====================================================================================================================================
# v8.10: cast, creative constitution, taste calibration, first-person POV rules, emotion curve vocabulary, impact recipe
# =====================================================================================================================================
# CAST (Settings CAST_ON): 5 experts (the Director role) + 15 rotating guests (the Curious One, still labelled [SKEPTIC] in scripts).
# PLACEHOLDER rows built on Google's 30 prebuilt voices: Setup seeds them once into an empty Cast tab; the owner overwrites them with the 20 chosen voices.
# "voice" = a prebuilt name (two speakers per request), a library voice id, or a designed "voice_..." id (voiced one line at a time).
CAST_COLUMNS = ("id", "role", "display_name", "voice", "gender", "pitch", "personality", "speech_habits", "signature_quirk", "style_direction",
                "intro_line", "active", "weight", "last_used")
CAST_SEED = [
 ("E1", "expert", "Dr. Vale", "Charon", "male", "low", "calm, precise, quietly amused by catastrophe", "short sentences, numbers said slowly", "says 'okay, freeze that' before every reveal", "measured, warm, low and close to the mic", "Welcome back to the simulation."),
 ("E2", "expert", "Professor Ines", "Kore", "female", "medium", "firm, curious, loves the weird detail", "asks a question then answers it", "counts down 'three, two...' and never says one", "firm and clear, a smile in the voice", "Okay. Simulation is loading."),
 ("E3", "expert", "Marcus", "Sadaltager", "male", "medium", "knowledgeable storyteller, slightly theatrical", "builds to the point with 'and then'", "names every object like it's a person", "knowledgeable, unhurried, rich", "Lights down. We're going in."),
 ("E4", "expert", "Dr. Okafor", "Gacrux", "female", "low", "mature, dry wit, has seen every disaster model", "understatement", "rates every catastrophe out of ten", "mature, dry, intimate", "Pull up a chair. This one's strange."),
 ("E5", "expert", "Theo", "Rasalgethi", "male", "medium", "informative, energetic teacher", "uses 'picture this' and real units", "taps the desk (says 'tap tap') when a number matters", "bright and informative, quick but clear", "Right. Strap in."),
 ("G1", "guest", "Jess", "Puck", "male", "medium", "upbeat barista, takes everything personally", "interrupts with 'wait wait wait'", "relates everything to coffee orders", "upbeat, quick, expressive", "Hi! Is this going to hurt?"),
 ("G2", "guest", "Rio", "Fenrir", "male", "medium", "excitable gamer", "gaming slang, kept clean", "asks for the 'respawn point'", "excitable, fast, big reactions", "Okay I am SO ready."),
 ("G3", "guest", "Maya", "Leda", "female", "high", "youthful art student, notices colours", "describes things by colour and texture", "names the colour of every disaster", "youthful, bright, wide-eyed", "Hi, I brought snacks."),
 ("G4", "guest", "Nora", "Aoede", "female", "medium", "breezy night-shift nurse, unshockable", "deadpan 'seen worse'", "triages the apocalypse out loud", "breezy, deadpan, relaxed", "Hey. Let's see what breaks."),
 ("G5", "guest", "Sam", "Zephyr", "female", "medium", "bright engineer, trusts numbers", "asks 'how many, exactly?'", "rounds every number to something edible", "bright, crisp, curious", "I have questions already."),
 ("G6", "guest", "Lena", "Laomedeia", "female", "high", "upbeat runner, competitive", "turns things into a race", "asks how fast she could outrun it", "upbeat, breathless energy", "Do I need running shoes?"),
 ("G7", "guest", "Dev", "Sadachbia", "male", "medium", "lively food truck cook", "food metaphors", "estimates everything in tacos", "lively, warm, playful", "Smells like trouble. Good."),
 ("G8", "guest", "Ari", "Achird", "male", "medium", "friendly new dad, sleep-deprived", "yawns mid-sentence", "worries about the baby monitor", "friendly, tired, soft laugh", "If I fall asleep, wake me."),
 ("G9", "guest", "Kai", "Zubenelgenubi", "male", "medium", "casual skater, fearless", "says 'no way' a lot", "wants to ride whatever is falling", "casual, laid back, grinning", "Sup. What are we breaking?"),
 ("G10", "guest", "Bea", "Callirrhoe", "female", "medium", "easy-going librarian, notices tiny details", "whispers when excited", "quietly corrects one tiny fact", "easy-going, soft, precise", "Hello. I read ahead."),
 ("G11", "guest", "Omar", "Umbriel", "male", "low", "easy-going truck driver, practical", "asks about traffic", "measures distance in hours of driving", "easy-going, low, practical", "Long haul today?"),
 ("G12", "guest", "Grant", "Algenib", "male", "low", "gravelly retired miner, unimpressed", "grumbles, then is amazed", "compares everything to a mine shaft", "gravelly, slow, warm underneath", "Seen a lot. Show me."),
 ("G13", "guest", "Hana", "Vindemiatrix", "female", "medium", "gentle yoga teacher", "breathes out before reacting", "tries to stay calm and fails", "gentle, breathy, soft", "Deep breath. Okay."),
 ("G14", "guest", "Zoe", "Despina", "female", "medium", "smooth podcaster, skeptical", "'hold on, source?'", "fact-checks the Director once per episode", "smooth, sceptical, sharp", "I'm not buying it. Yet."),
 ("G15", "guest", "Eli", "Enceladus", "male", "medium", "breathy nervous accountant", "nervous laugh", "calculates the insurance claim", "breathy, nervous, endearing", "Is this... covered?"),
]
def cast_seed_rows():
    return [dict(zip(CAST_COLUMNS, list(r) + ["TRUE", "1", ""])) for r in CAST_SEED]
PREBUILT_VOICES = ("Zephyr", "Puck", "Charon", "Kore", "Fenrir", "Leda", "Orus", "Aoede", "Callirrhoe", "Autonoe", "Enceladus", "Iapetus", "Umbriel", "Algieba",
                   "Despina", "Erinome", "Algenib", "Rasalgethi", "Laomedeia", "Achernar", "Alnilam", "Schedar", "Gacrux", "Pulcherrima", "Achird",
                   "Zubenelgenubi", "Vindemiatrix", "Sadachbia", "Sadaltager", "Sulafat")      # Google's 30 prebuilt studio voices (docs, Oct 2026)

# The Creative Constitution: the built-in default (Settings CONSTITUTION replaces it). Every department reads it, above its own brief.
CONSTITUTION = """CREATIVE CONSTITUTION (the owner's standing rules for every episode; they outrank habits, never the safety rules):
1. The viewer is INSIDE the scene. First person: the camera is the falling object or the viewer's own eyes; present tense, second person ('you feel...').
2. Weird but showable: a topic that makes a tired scroller think 'what kind of topic is this?', explained by real physics, and SHOWN, not lectured.
3. A podcast, not a lecture: an expert and a guest who react with their bodies (breath, a gasp, a nervous laugh), never a lecture with a sidekick.
4. Low background noise. The voice is always the clearest thing. Silence is a tool, not an accident.
5. ASMR textures: close, tactile sounds (a creak, a drip, glass ticking, fabric) under the key moments.
6. Restraint and implication, like low-budget psychological suspense: withhold, suggest, hold the silence, cut to black before the obvious.
7. Every video is treated as the most important project we have ever made."""

# Taste calibration (owner's examples). Liked = scroll-stopping, impossible-sounding, yet physically showable and personal.
TASTE_LIKED = ["What if Saturn's rings were for sale?", "What if only you could sense Wi-Fi signals?",
               "What if the inside of a volcano were moved next to your city?", "What if your hair aged 50 years in one day?"]
TASTE_BORING = ["What if all tears on Earth doubled in size?", "What if your lunch break skipped ahead without warning?",
                "What if chewing gum became addictive overnight?", "What if mushrooms turned to glass?",
                "What if yesterday moved ten times slower for you only?"]
TASTE_NOTE = ("LIKED ones break a rule of reality in a way you can SEE in first person and that touches YOU (your city, your hair, your senses, owning a planet's rings). "
              "BORING ones are small, abstract or unshowable (a duration, a habit, a property nobody can picture changing), or weird without a picture.")
PREMISE_CRITERIA = ("weirdness", "counterintuitive_explainable", "showable_pov", "self_relevance", "emotional_peak", "novelty", "headline_fit")

# First-person POV rules (v8.10, owner rule: applied to EVERY shot type: stills, living stills, Kling clips; stock and graphics get the camera effects).
POV_STILL = ("first-person POV, the camera IS the viewer's eyes, foreground anchor in frame ({anchor}), extreme wide lens 14mm, "
             "strong perspective, slight motion blur at the edges, viewer inside the scene")
POV_LIVING = ("first-person POV, camera at eye level inside the scene, slow breathing sway, foreground {anchor} drifting, particles passing close to the lens, "
              "parallax between near and far")
POV_KLING = ("first-person POV, camera mounted on the moving object, accelerating, shaking, debris streaking past the lens, heat shimmer, "
             "extreme wide lens, motion blur, foreground {anchor}")
POV_ANCHORS = ((r"helmet|astronaut|space|orbit|planet|moon|saturn|ring", "the rim of a helmet visor"), (r"fall|drop|sky|plane|parachut", "your own hands reaching out"),
               (r"fire|lava|volcan|heat|burn", "heat shimmer and your hands shielding your face"), (r"water|ocean|flood|wave|rain", "water droplets on the lens"),
               (r"car|road|drive|street|city", "a windshield edge and dashboard"), (r"hair|skin|body|hand|bone", "your own hands in the lower frame"))
POV_ANCHOR_DEFAULT = "your own hands in the lower frame"
VANTAGES = ("eyes", "object", "hands", "helmet", "vehicle", "ground")
# Delivery curve vocabulary the writer may put in {braces} after the tags. Never spoken. Gemini acts all of it; Kokoro uses the pace words only.
CURVE_WORDS = {"slow": "speaking slowly", "fast": "speaking quickly", "low": "low pitch", "high": "higher pitch", "soft": "soft, quiet", "loud": "louder, projecting",
               "whisper": "whispering", "hushed": "hushed, close to the mic", "rising": "energy rising through the line", "falling": "energy falling away",
               "shaky": "voice shaking", "breathless": "out of breath", "tense": "tense", "warm": "warm", "awed": "awed, almost reverent", "dry": "dry, deadpan"}
CURVE_EVENTS = {"breath": "<breath>", "gasp": "<gasp>", "laugh": "<laugh>", "chuckle": "<chuckle>", "sigh": "<sigh>", "exhale": "<exhales>", "pant": "<pant>"}
# Our delivery tags -> Gemini turn style + an optional inline event at the start of the line.
TAG_STYLE = {"calm": ("calm, unhurried", ""), "tension": ("tense, low and urgent", ""), "reveal": ("slow, weighty reveal", "<breath>"),
             "aside": ("wry, lighter aside", ""), "callback": ("knowing, warm callback", ""), "close": ("hushed, intimate, close to the mic", ""),
             "wow": ("bright, amazed", ""), "gasp": ("shocked", "<gasp>"), "awe": ("awed, breathy and slow", "<breath>"), "laugh": ("laughing", "<laugh>"),
             "doubt": ("doubtful, sceptical", ""), "patient": ("patient, reassuring", ""), "none": ("", "")}
# The impact recipe (sound + camera locked together): rumble+riser -> 1-2 beats of near-silence -> boom + sub drop -> ringing + muffled heartbeat/breath -> recovery.
IMPACT_RECIPE = (("rumble_riser", -3.0, 3.0), ("near_silence", 0.0, 0.0), ("boom_sub", 0.0, 2.2), ("ring_heartbeat", 0.15, 4.0), ("recovery", 4.0, 3.0))
