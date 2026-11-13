"""v9.1 paid-call counter: produces ONE episode with the fakes and counts every call that is paid in real life (text-model calls by role, vision checks,
images, image-to-video, TTS requests, batch submissions). Frozen clock + fixed slot, so the count is reproducible."""
import collections, datetime as dt

FROZEN = dt.datetime(2026, 11, 5, 9, 30, 7, tzinfo=dt.timezone.utc)

def watch(monkeypatch):
    """Count every call that is paid in real life from here on (the returned Counter fills as production runs)."""
    from whatifs import models as M, media as MD
    c = collections.Counter()
    ra = M.ask
    def ask(role, *a, **k): c["text:" + str(role)] += 1; return ra(role, *a, **k)
    monkeypatch.setattr(M, "ask", ask)
    for mod in __import__("sys").modules.values():
        if getattr(mod, "__name__", "").startswith("whatifs.") and getattr(mod, "ask", None) is ra: monkeypatch.setattr(mod, "ask", ask)
    rv = M.ask_vision; monkeypatch.setattr(M, "ask_vision", lambda *a, **k: (c.update(["vision"]), rv(*a, **k))[1])
    rs = MD.still; monkeypatch.setattr(MD, "still", lambda *a, **k: (c.update(["image_premium" if k.get("premium") else "image"]), rs(*a, **k))[1])
    rn = MD.animate; monkeypatch.setattr(MD, "animate", lambda *a, **k: (c.update(["clip_kling" if k.get("hero") else "clip"]), rn(*a, **k))[1])
    from whatifs import anim as AN                                   # v10.2: reference-locked start frames from Google's image model are a paid call too
    rg = AN.gemini_image; monkeypatch.setattr(AN, "gemini_image", lambda *a, **k: (c.update(["image_ref"]), rg(*a, **k))[1])
    if hasattr(M, "ask_batch"):
        rb = M.ask_batch; monkeypatch.setattr(M, "ask_batch", lambda *a, **k: (c.update(["batch"]), rb(*a, **k))[1])
    # v12 V2c-b2b: two kinds of paid call the counter never saw, because other modules hold their own name for the function - the key art (the thumbnail,
    # its runner-up; until this batch also two reel covers) and a voice job (the narration; until this batch also one per cut-down reel).
    import sys
    from whatifs import voice as V
    def still_(*a, **k): c["image_premium" if k.get("premium") else "image"] += 1; return rs(*a, **k)
    rv_ = V.narrate
    def narrate_(*a, **k): c["voice_job"] += 1; return rv_(*a, **k)
    for mod in list(sys.modules.values()):
        if not getattr(mod, "__name__", "").startswith("whatifs.") or mod is MD: continue
        if getattr(mod, "still", None) is rs: monkeypatch.setattr(mod, "still", still_)
        if getattr(mod, "narrate", None) is rv_: monkeypatch.setattr(mod, "narrate", narrate_)
    return c

def count(monkeypatch, tmp_path):
    from tools.rehearsal import ToneVoice
    import whatifs.voice as V
    from whatifs import core, manage as MG, episode as EP
    monkeypatch.setattr(V, "KokoroBackend", lambda blend: ToneVoice()); MG.setup(); core.set_setting("VOICE", "C")
    monkeypatch.setattr(EP, "now_utc", lambda: FROZEN)
    c = watch(monkeypatch)
    slot = (FROZEN + dt.timedelta(hours=10)).strftime("%Y-%m-%dT%H:%M:%SZ")
    r = EP.produce(slot)
    return dict(c), r

# v10.2 (owner decision 9 Nov 2026, option C + the Feature Contract): the ONLY paid calls allowed beyond the v9 baseline.
V102_ADDED = {"clip_kling": 1,      # 4 animated scenes instead of 3 (Kling on fal)
              "image_ref": 4,       # one reference-locked start frame per animated scene (Google image model)
              "text:critic": 1,     # the 6-point creative self-review (Gemini judge)
              "image": 3,           # the 4 scenes sit at the retention cliffs, so up to 3 more shots carry their own picture (FLUX, about Rs 0.6 each)
              "clip": 1}            # one more living still where a scene slot displaced the opening layout (about Rs 2)

# v11 Stage B (room v2, owner-approved 9 Nov 2026): role memos + objections are gone (fewer calls); these are the ONLY additions.
def V11_ADDED():
    from whatifs.core import S
    j = S("JURY_ORDERINGS", int); slots = S("JOKE_SLOTS", int)
    return {"text:writer": S("ROOM_V2_DRAFTS", int) - 1,      # 3 diverse drafts instead of 1 (Opus)
            "text:rewrite": 1,                                # the one checklist revision
            "text:punchup": 1,                                # one call writes every joke slot's alternatives (Sonnet)
            "text:jury": j + slots,                           # Gemini Pro: drafts (both orders) + one ranking per joke slot
            "text:jury_flash": j,                             # Gemini Flash: drafts only
            "text:jury_claude": j + slots,                    # Claude Sonnet (never the writer): drafts + joke slots
            "image": 1}                                       # a v2 script can plan one more shot than the v1 fake (+Rs 0.5)

# v11.1 (hard enforcement): ONE mandatory rewrite when retention / marker problems remain after the last rewrite (enforce.fix_all, ~Rs 2).
V111_ADDED = {"text:rewrite": 1}

# v12 V1 (the viewer's seat): number graphics that leave the opening become pictures. Where the opening or the repetition guard wants a fresh one it is
# a paid still (under Rs 1): 2 in the fake episode. No text call is added (the numbers problem rides on the ONE mandatory rewrite that already exists).
V12V1_ADDED = {"image": 2}

# v12 V1b (the layman test): the promise line-up - one small call to a cheap reader of each model family, once per video (saved with the plan).
V12V1B_ADDED = {"text:probe_gemini": 1, "text:probe_claude": 1}

# v12 V2c-b2b1 (the opening): what a long video that opens on its Short's footage NO LONGER pays, against one that opens on pictures of its own (a video
# under an override; every video of the older tests, which run with the ladder off - so the baseline above is unchanged). tests/test_v12_opening_e2e.py
# makes both and compares.
V12V2CB2B_REMOVED = {"clip_kling": 1,     # the animated scene at second 0: the Short's footage is there, already paid (about Rs 39)
                     "image_ref": 1,      # ... and its reference-locked start frame (about Rs 6)
                     "text:hooks": 1,     # the hook lab's ten lines: the first line is the Short's own hook
                     "text:critic": 1}    # ... and the judge of those ten lines

# v12 V2c-b2b (the cut-downs): since this batch the counter also sees the key art and the voice jobs (always paid, never counted: other modules hold their
# own name for the function). As the code made them BEFORE this batch - measured on the accepted code of V2c-b2b1 with this counter:
V12V2CB2C_COUNTED = {"image_premium": 4,     # the thumbnail, its runner-up and two reel covers
                     "voice_job": 5}         # the narration and one voice job per cut-down reel
# ... and what a long video NO LONGER pays, because it makes no cut-down reels (measured: every other count is unchanged):
V12V2CB2C_REMOVED = {"text:reels": 1,        # the cut-downs' planning call (the editing model)
                     "image_premium": 2,     # two reel covers of premium key art
                     "voice_job": 4}         # four reels spoken again by the voices

# v12 V2d (the money and the model): NO paid call is added and none is removed. What changed is what a call BUYS and what the estimate says about it:
# a hero clip is bought by the second (its Cost_Log units are seconds), and every key this counter counts is named by a line of the one cost model
# (`whatifs/costguard.py:lines`, field `calls`) - `tests/test_v12_money.py` makes whole productions and compares the two call by call: clip_kling,
# image_ref, image_premium and voice_job must be EQUAL to their lines (4 / 4 / 2 / 1 for a long video on its own pictures, 3 / 3 / 2 / 1 for one about a
# promoted Short), image and clip may not exceed theirs, and every text call needs the writing line.
# v12 V2d-b (the ladder's rules): a shot of real footage that breaks the stock rules becomes a PICTURE OF OUR OWN (never first, never two in a row, only on
# a line of 2 to 4 seconds, a tenth of the film at most). The offline Director asks for real footage on every seventh line; in the fake episode two of them
# sit on lines too long for an anchor (up to 3 more paid stills). And A CHARACTER IS DRAWN OR ABSENT: the tiny line of a character without approved art is
# no longer a free cutaway with a drawn shape - it is a picture line like any other and may get a picture of its own (up to 7 more in the fake episode,
# which has no approved cast). Under Rs 1 each, about Rs 6 a video at most; a still is a ceiling of the estimate's stills line. Counted with this counter:
# 26 before, 36 now; every other count is unchanged. (Letting such a line re-use the picture before instead - no picture bought - was tried while
# building and raised the flash-safety check on one offline episode: BUILD_STATE, open issue 164.)
V12V2DB_ADDED = {"image": 10}

def allowed_base(base):
    out = dict(base)
    for k, v in V12V2CB2C_COUNTED.items(): out[k] = out.get(k, 0) + v
    for k, v in V12V2CB2C_REMOVED.items(): out[k] = out.get(k, 0) - v
    for k, v in V102_ADDED.items(): out[k] = out.get(k, 0) + v
    for k, v in V11_ADDED().items(): out[k] = out.get(k, 0) + v
    for k, v in V111_ADDED.items(): out[k] = out.get(k, 0) + v
    for k, v in V12V1_ADDED.items(): out[k] = out.get(k, 0) + v
    for k, v in V12V1B_ADDED.items(): out[k] = out.get(k, 0) + v
    for k, v in V12V2DB_ADDED.items(): out[k] = out.get(k, 0) + v
    return out

