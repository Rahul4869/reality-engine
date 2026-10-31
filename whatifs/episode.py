"""whatifs/episode.py v8.9 - one full episode, in three resumable stages (v8.5: fresh opening pictures, up to 4 Shorts, B thumbnail):
  PLAN    AI writing, hooks, narration (the master clock), shots, packaging text, reel plans      -> checkpoint "plan"
  ASSETS  every paid picture and clip (retried individually, only the missing ones on a resume)   -> checkpoint "assets"
  FINISH  render -> thumbnail + covers + reels -> full QC (+ free fixes) -> upload scheduled, or HOLD with a one-click fix
Long video is uploaded PRIVATE with publishAt = slot. Reels go out 15 min and 6 h after it is live, reels 3-4 the next two days (separate 'release' job).
Nothing that fails final QC is ever uploaded. A retry of the same slot resumes from the newest checkpoint instead of paying for the plan and assets again."""
from __future__ import annotations
import os, json, re, time, datetime as dt, concurrent.futures as cf
from PIL import Image
from whatifs.core import S, log, store, iso, JOB, WORK, FAKE, SMALL, flush_log, now_utc, set_setting, scrub, env, month_spend, refresh_spend, take_degraded, note_degraded
from whatifs import room as ROOM, media as M, render as RN, art as ART, reels as REELS, qc as QC, publish as PUB, hooks as HOOKS, cutmap as CUTMAP, tableread as TR
from whatifs import reactions as RX, checkpoint as CK, fixes as FIX, preflight as PF
from whatifs.voice import narrate, Blend, NarrationResult
from whatifs.sampler import draw as DRAW
from whatifs.governor import plan_for_episode, fal_allowed, episodes_left_this_month
from whatifs import governor as G
from whatifs import growth as GR
from whatifs import format_engine as FE, cta as CTA
from whatifs import sound as SD

BLENDS = {        # v8.9 clarity: two voices at most, one dominant, only Kokoro's best-graded voices (am_onyx, graded D, and bm_george removed: they made the mix dense)
    "A": {"am_michael": 0.70, "am_fenrir": 0.30},
    "B": {"am_fenrir": 0.65, "am_michael": 0.35},
    "C": {"af_heart": 0.80, "af_bella": 0.20},
    "D": {"af_bella": 0.75, "af_heart": 0.25},
}
def speaker_blends(guest=None):
    """The two recurring roles get their own voice recipes (Settings DIRECTOR_VOICE / SKEPTIC_VOICE). Always two DIFFERENT recipes. None in classic mode.
    v8.9: with GUEST_ROTATION_ON the Curious One is this episode's guest (data.GUESTS, chosen in the draw and saved with the plan, so a retry and the reels
    use the same voice)."""
    if FE.mode() == "classic": return None
    from whatifs.data import GUESTS
    d = (S("DIRECTOR_VOICE") or "B").strip().upper()[:1]; k = (S("SKEPTIC_VOICE") or "C").strip().upper()[:1]
    if d not in BLENDS: d = "B"
    if k not in BLENDS or k == d: k = next(x for x in "CDBA" if x != d)
    sk = Blend("skeptic", BLENDS[k])
    if guest in GUESTS and S("GUEST_ROTATION_ON", bool): sk = Blend("guest_" + guest, GUESTS[guest][1])
    return {"DIRECTOR": Blend("director", BLENDS[d]), "SKEPTIC": sk}

def blend():
    v = (S("VOICE") or "A").strip().upper()
    if "+" in v:  # e.g. "A+C" = 50/50 mix of two recipes
        parts = {}
        for k in v.split("+"):
            for n, wgt in BLENDS.get(k.strip(), BLENDS["A"]).items(): parts[n] = parts.get(n, 0) + wgt / 2
        return Blend("custom", parts)
    return Blend(v, BLENDS.get(v, BLENDS["A"]))

def est_cost_inr(d):
    u = S("USD_INR", float)
    return u * (d["stills"] * S("PRICE_STILL_USD", float) + G.premium_images() * S("PRICE_THUMB_USD", float) + d["living"] * S("PRICE_LIVING_USD", float)
                + d["kling"] * S("PRICE_KLING_USD", float)) + S("LLM_EST_INR", float) \
        + (S("TABLE_READ_EXTRA_INR", float) if TR.active_arm(d.get("episode_id", ""))[0] == "on" else 0.0)

def chapters(timeline, beats_at):
    ch = [("0:00", "Intro")]
    for i, (t, name) in enumerate(beats_at):
        if t < 10 or t - _sec(ch[-1][0]) < 45: continue
        ch.append((f"{int(t//60)}:{int(t%60):02d}", name[:40]))
    return ch if len(ch) >= 3 else ch[:1]
def _sec(s): m, x = s.split(":"); return int(m) * 60 + int(x)


# =====================================================================================================================================
# v8.2: stages, resume, the render job (what the QC fixes act on), hold and one-click fix
# =====================================================================================================================================
def _apply_tier(d, plan):
    """The budget tier is applied BEFORE anything is written, so the room plans inside it instead of being trimmed afterwards."""
    lo = S("RUNTIME_MIN_SEC", int) + 15
    d["runtime_sec"] = int(max(lo, min(d["runtime_sec"], plan.get("runtime_cap", d["runtime_sec"]))))
    d["words"] = int(d["runtime_sec"] / 60 * S("WPM_ESTIMATE", float))
    d["stills"] = min(d["stills"], plan.get("stills", d["stills"]))
    d["budget"] = {k: plan.get(k) for k in ("tier", "reason")}

def _preflight_mail(why):
    day = now_utc().strftime("%Y-%m-%d")
    if S("PREFLIGHT_MAIL_DAY") != day:
        set_setting("PREFLIGHT_MAIL_DAY", day)
        PUB.email("Production paused: a health check failed", f"<p>Nothing was spent. A free pre-flight check found: {why}.</p><p>It is checked again every half hour and production starts by itself once it is green. "
                  "If it says a key is missing, add it under Settings > Secrets and variables > Actions on GitHub.</p>")

def _resumable(slot_iso):
    """A failed attempt for this slot that left a checkpoint: a retry resumes from it (the AI writing and the paid pictures are not paid for twice)."""
    for e in reversed(store().rows("Episodes")):
        if e.get("slot_et") == slot_iso and e.get("status") == "FAILED" and not e.get("yt_id") and CK.has(e) and CK.attempts(e) < 2: return e
    return None

def _stage_plan(ep, out, eps_left, slot_iso):
    """Steps 1-3 of an episode. Returns a JSON-able state dict (this is what the 'plan' checkpoint stores)."""
    st = store(); eps_left = eps_left or episodes_left_this_month()
    d = DRAW(ep, "collective"); d["slot"] = slot_iso
    plan = plan_for_episode(est_cost_inr(d), eps_left)
    if plan.get("hold"): raise RuntimeError(plan["reason"] + " - nothing was spent; the slot is skipped (budget gate)")
    d["kling"], d["living"] = plan["kling"], plan["living"]; _apply_tier(d, plan)
    d["reel_style"] = ROOM.reel_style()                     # v8.5: recorded so the learning job can compare reel styles by Shorts -> long-video views
    log(f"draw: {json.dumps(d)} | spend plan: {plan['reason']}")
    room = ROOM.run_room(d, ep)
    d["ptype"] = room["spine"].get("ptype", d["ptype"])
    if room["spine"].get("family"): d["strategies"]["family"] = room["spine"]["family"]; d["family"] = room["spine"]["family"]
    st.update("Episodes", "episode_id", ep, {"premise": room["spine"]["premise"], "ptype": d["ptype"], "presentation_format": room["spine"].get("presentation_format", "classic"),
                                              "status": "VOICING", "draw_json": d, "updated": iso()})
    _mark_premise(room["spine"]["premise"], ep)
    script = room["script"]["script"]
    script, hook_rec = HOOKS.run_hooks(script, room["spine"], ep, out)
    room["script"]["script"] = script
    beat_names = [b.get("purpose", f"Part {b.get('n')}") for b in room["bible"].get("beats", [])]
    clean, beat_marks = _strip_beats(script)
    hook = RX.ensure_units if FE.mode() != "classic" else None
    vkw = dict(style=d["strategies"]["voice"] or "slow_burn", seed=ep, speaker_blends=speaker_blends(d.get("guest")), unit_hook=hook)
    vo = narrate(clean, blend(), os.path.join(out, "voice"), **vkw)
    floor = 20 if SMALL else S("RUNTIME_MIN_SEC", int) + 3
    for attempt in range(2):
        if vo.duration >= floor: break
        short = floor - vo.duration; add_words = int(short / 60 * S("WPM_ESTIMATE", float) * 1.25) + 40
        log(f"narration {vo.duration:.0f}s is under {floor}s - asking the writer for ~{add_words} more words (free step)", "WARN")
        longer = ROOM.extend(room, script, add_words, ep)
        if longer: script = longer; clean, beat_marks = _strip_beats(script)
        vo = narrate(clean, blend(), os.path.join(out, "voice"), **vkw)
    if vo.duration < floor:
        raise RuntimeError(f"narration {vo.duration:.0f}s still under {floor}s - not spending on visuals; will retry")
    room["script"]["script"] = script
    tl = json.load(open(vo.timeline_path)); units = tl["units"]
    if tl.get("voice_fallback") and not S("VOICE_FALLBACK_OK", bool):
        raise RuntimeError(f"character voice {tl['voice_fallback']} could not load - stopping before any picture money is spent (a third narrator voice is never used); will retry")
    if hook_rec: HOOKS.verify_in_narration(hook_rec, units); _save_hook_final(hook_rec, out)
    log(f"narration {vo.duration:.1f}s, {len(units)} units, voice {vo.voiceprint}" + (f", character voice fallback for {tl['voice_fallback']}" if tl.get("voice_fallback") else ""))
    beats_at = [(units[i]["start"], beat_names[k] if k < len(beat_names) else f"Part {k+1}") for k, i in enumerate(beat_marks) if i < len(units)]
    chs = chapters(tl, beats_at)
    d["duration_sec"] = round(vo.duration, 1); d["beat_map"] = [[round(float(t), 1), str(n)[:40]] for t, n in beats_at][:24]      # v8.7: retention dips are mapped to beats
    pkg = tidy_pkg(ROOM.package(room, chs, d, ep))          # v8.6: title + thumbnail are decided BEFORE the shots (the opening must pay off the click)
    shots = ROOM.plan_shots(room, units, d, plan, ep)
    sync = ROOM.continuity({"script": clean[:20000], "shots": shots[:80], "spine": room["spine"]}, ep)
    if not sync.get("ok", True) and sync.get("problems"):
        log(f"continuity problems: {sync['problems'][:5]} - re-planning shots once", "WARN", public=f"continuity problems ({len(sync['problems'])}) - re-planning shots once (details kept private)")
        room["bible"]["look"] = room["bible"].get("look", "") + " | fix: " + "; ".join(p.get("fix", "") for p in sync["problems"][:5])
        shots = ROOM.plan_shots(room, units, d, plan, ep)
    shots = ROOM.promise_shot(shots, units, pkg)            # v8.6: the first opening Kling clip shows the thumbnail's scene
    if S("SOUND_DESIGN_ON", bool): shots = SD.plan_sounds(shots, units, SD.density_of(d["strategies"].get("sound")))      # v8.7: close textures under the shots that show them
    if not pkg.get("thumb_prompt") and (d.get("promise") or {}).get("thumb_scene"): pkg["thumb_prompt"] = d["promise"]["thumb_scene"]
    st.update("Episodes", "episode_id", ep, {"draw_json": d, "updated": iso()})          # v8.7: promise, rhythm plan, retention check, beat map, playbook flags
    rplans = ROOM.reels(room, shots, d, ep)
    return {"ep": ep, "slot": slot_iso, "d": d, "plan": plan, "room": room, "hook_rec": hook_rec, "shots": shots, "pkg": pkg, "rplans": rplans, "chs": chs,
            "vo": {"wav": os.path.basename(vo.wav_path), "timeline": os.path.basename(vo.timeline_path), "duration": vo.duration, "voiceprint": vo.voiceprint, "style": vo.style}}

def consume_tease(S_):
    """v8.9.1: clear NEXT_PREMISE once the episode that used it has a saved plan. Only if the cell still holds THAT premise (a newer tease is never wiped).
    Before v8.9.1 it was cleared the moment the scout ran, so any failure while planning lost the promise made at the end of the last video."""
    tp = str(((S_ or {}).get("room") or {}).get("spine", {}).get("teased_premise") or "").strip()
    if not tp: return False
    try: cur = json.loads(S("NEXT_PREMISE") or "{}").get("premise", "")
    except Exception: cur = ""
    if str(cur).strip().lower() != tp.lower(): return False
    set_setting("NEXT_PREMISE", ""); return True

def _vo_of(S_, out):
    v = S_["vo"]; return NarrationResult(os.path.join(out, v["wav"]), os.path.join(out, v["timeline"]), v["duration"], v["voiceprint"], v["style"])

def _assets_state(files):
    b = os.path.basename
    return {"img": {str(i): b(p) for i, p in files["img"].items()}, "clips": {str(i): b(p) for i, p in files["clips"].items()}, "anchors": files["anchors"],
            "urls": {str(i): u for i, u in (files.get("urls") or {}).items() if u}}      # v8.9.1: picture URLs survive a resume (no paid re-make just to get a URL)

def _load_assets(out):
    """Pictures and clips restored from a checkpoint (paths re-based to this machine)."""
    p = os.path.join(out, "assets.json")
    if not os.path.exists(p): return None
    a = json.load(open(p))
    return {"img": {int(i): os.path.join(out, n) for i, n in a["img"].items() if os.path.exists(os.path.join(out, n))},
            "clips": {int(i): os.path.join(out, n) for i, n in a["clips"].items() if os.path.exists(os.path.join(out, n))}, "anchors": a.get("anchors", []), "segments": {},
            "urls": {int(i): u for i, u in (a.get("urls") or {}).items() if u}}

def anchor_shots(shots, budget, max_run=None, opening=()):
    """Which shots get a NEW picture. Kling and living clips always do; then the Director's hero shots (consequences, new places, peaks); then the rest of the
    budget spread evenly. Finally a repetition guard: if more than FREE_SHOT_MAX_RUN consecutive shots would share one picture, a fresh picture is added in the middle
    of the run (a still costs under Rs 1, so a few extra beat any visible repetition). Every other shot re-uses the nearest earlier picture with its own crop and grade."""
    max_run = max_run or S("FREE_SHOT_MAX_RUN", int)
    own = [i for i, s in enumerate(shots) if s["type"] in ("living", "kling")]
    stills = [i for i, s in enumerate(shots) if s["type"] == "still"]
    left = max(0, budget - len(own)); a = set(own)
    if opening and S("OPENING_FRESH_ON", bool):               # v8.5: every opening shot gets its own picture (fast, fresh cuts while viewers decide); taken from the same budget
        op = [i for i in stills if i in set(opening)][:left]; a |= set(op); left -= len(op)
    heroes = [i for i in stills if shots[i].get("hero") and i not in a][:left]; a |= set(heroes); left -= len(heroes)
    rest = [i for i in stills if i not in a]
    if rest and left > 0:
        step = len(rest) / min(left, len(rest)); a |= {rest[int(k * step)] for k in range(min(left, len(rest)))}
    first = next((i for i, s in enumerate(shots) if s["type"] in ("still", "graphic")), None)
    if first is not None and not (a & set(range(0, first + 1))): a.add(first)
    extra = 0
    while extra < 12:                                           # repetition guard
        run_start = None; worst = (0, 0, 0)
        for i, s in enumerate(shots):
            if i in a or s["type"] in ("stock", "graphic"): run_start = None; continue
            if run_start is None: run_start = i
            n = i - run_start + 1
            if n > worst[0]: worst = (n, run_start, i)
        if worst[0] <= max_run: break
        a.add((worst[1] + worst[2]) // 2 if shots[(worst[1] + worst[2]) // 2]["type"] == "still" else worst[1]); extra += 1
    return sorted(a)

def _assets(shots, units, out, ep, budget=56, have=None):
    """Pictures only for anchor shots, then clips. Each failed asset is retried (a Kling clip KLING_RETRY_MAX times); what still fails is reported in files['missing'] /
    files['delivered'] and judged by final QC. have = assets restored from a checkpoint: only what is missing is made (and paid for)."""
    opening = set(ROOM.opening_units(units)); anchors = anchor_shots(shots, budget, opening=sorted(opening))
    img_paths = dict((have or {}).get("img", {})); clips = dict((have or {}).get("clips", {})); img_urls = {i: u for i, u in ((have or {}).get("urls") or {}).items() if i in img_paths}
    def get_img(i):
        s = shots[i]; p = os.path.join(out, f"img{i:03d}.jpg"); last = None
        for attempt in range(2):
            try:
                path, url = M.still(s.get("prompt") or units[i]["text"], p, ep, seed=f"{ep}{i}{attempt}"); return i, path, url
            except Exception as e: last = e; time.sleep(2)
        log(f"image {i} failed twice: {last}", "WARN"); return i, None, None
    todo = [i for i in anchors if i not in img_paths]      # v8.9.1: a restored picture without its URL is animated from the file itself (media.animate), never paid for again
    with cf.ThreadPoolExecutor(max_workers=6) as ex:
        for i, p, u in ex.map(get_img, todo):
            if p: img_paths[i] = p; img_urls[i] = u
    def get_clip(i):
        s = shots[i]; p = os.path.join(out, f"clip{i:03d}.mp4"); tries = 1 + (S("KLING_RETRY_MAX", int) if s["type"] == "kling" else 1)
        for attempt in range(tries):
            try:
                if s["type"] == "stock": return i, M.stock(s.get("search", "space"), p, ep)
                if s["type"] in ("living", "kling") and i in img_paths:
                    return i, M.animate(img_urls.get(i), img_paths[i], motion_prompt(s, units[i]["text"], i in opening), p, ep, hero=s["type"] == "kling")
                return i, None
            except Exception as e: log(f"clip {i} failed ({s['type']}, try {attempt + 1}/{tries}): {e}", "WARN"); time.sleep(3)
        log(f"clip {i} gave up ({s['type']}) -> still", "WARN"); return i, None
    need_clip = [i for i, s in enumerate(shots) if s["type"] in ("stock", "living", "kling") and i not in clips]
    with cf.ThreadPoolExecutor(max_workers=3) as ex:
        for i, c in ex.map(get_clip, need_clip):
            if c: clips[i] = c
    delivered = {"kling": sum(1 for i, s in enumerate(shots) if s["type"] == "kling" and i in clips), "living": sum(1 for i, s in enumerate(shots) if s["type"] == "living" and i in clips)}
    return {"img": img_paths, "clips": clips, "segments": {}, "anchors": anchors, "missing": [i for i in anchors if i not in img_paths], "delivered": delivered, "urls": img_urls}

class Job:
    """The finishing stage's working state: what the render needs and what the QC fixes act on."""
    def __init__(self, **kw): self.__dict__.update(kw); self.segmeta = []; self.events = []; self.mixpath = None; self.video = None; self.master = None; self.fixn = 0
    # ---- full render from the assets and the narration clock
    def render_all(self):
        self.files["segments"] = {}; self.segmeta = []; self.master = _render(self); return self.master
    def own(self): return set(self.files["img"]) | set(self.files["clips"])
    def qc_ctx(self):
        return {"master": self.master, "duration": self.vo.duration, "fps": self.fps, "wav": self.vo.wav_path, "srt": self.srt, "timeline": self.tl, "units": self.units,
                "shots": self.shots, "own": self.own(), "delivered": self.files.get("delivered", {}), "kling_min": S("KLING_MIN_CLIPS", int),
                "missing_images": [i for i in self.files.get("anchors", []) if i not in self.files["img"]], "episode": self.ep}
    # ---- fixes
    def remix(self, lufs):
        mix = RN.score(self.vo.duration, self.ep, self.events, self.vo.wav_path, design=getattr(self, "design", None)); aud = RN.write_mix(mix, os.path.join(self.out, "mix.wav"), lufs=lufs)
        self.master = RN.mux(self.video, aud, os.path.join(self.out, "master.mp4")); return self.master
    def rebuild_captions(self): RN.srt(self.tl, self.srt); return self.srt
    def rebuild_video(self):
        self.video = RN.concat([m["path"] for m in self.segmeta], os.path.join(self.out, "video.mp4"))
        aud = os.path.join(self.out, "mix.wav")
        self.master = RN.mux(self.video, aud, os.path.join(self.out, "master.mp4")); return self.master
    def rerender_times(self, times):
        """Re-render only the segments around the given seconds (a black or frozen stretch) with a different crop and grade, then re-stitch."""
        self.fixn += 1; fps = self.fps; hit = [m for m in self.segmeta if any(m["f0"] / fps - 1.0 <= t <= (m["f0"] + m["nf"]) / fps + 1.0 for t in times)]
        RN.set_overlay(self.overlay)
        for m in hit:
            img = m.get("img") or next((p for _, p in sorted(self.files["img"].items())), None); RN.set_cursor(m["f0"])
            try:
                if img: RN.parallax_segment(img, m["path"], m["nf"], seed=f"{self.ep}fix{self.fixn}{m['i']}", detail=True, focus="center", look=RN.LOOKS[self.fixn % len(RN.LOOKS)])
                else: RN.graphic_segment({"label": "", "from": 0, "to": 0}, None, m["path"], m["nf"])
            except Exception as e:
                log(f"segment {m['i']} re-render failed: {e} -> plain fallback", "WARN"); RN.graphic_segment({"label": "", "from": 0, "to": 0}, img, m["path"], m["nf"])
        RN.set_overlay(None); return self.rebuild_video()
    def repair_assets(self, codes, idx, cap_inr):
        """Paid repair, capped in rupees: re-make missing pictures, failed Kling clips and the pictures a vision check flagged; then one free re-render."""
        base = month_spend(); done = False; f = self.files; shots, units = self.shots, self.units
        def spent(): return month_spend() - base
        def anchor_of(i):
            return i if i in f["img"] else next((j for j in range(i, -1, -1) if j in f["img"]), i)
        targets = set(f.get("missing", [])) | {i for i in f["anchors"] if i not in f["img"]}
        if codes & {"vision_mismatch", "vision_artifact"}: targets |= {anchor_of(i) for i in idx or []}
        if "reuse_run" in codes:
            run = [i for i, s in enumerate(shots) if s["type"] == "still" and i not in self.own()]
            if run: targets.add(run[len(run) // 2])
        for i in sorted(targets):
            if spent() >= cap_inr: break
            try:
                p = os.path.join(self.out, f"img{i:03d}.jpg"); txt = units[i]["text"][:140]
                path, url = M.still(f"{shots[i].get('prompt') or txt}. Clear, sharp, no text in the picture, accurate to this line: {txt}", p, self.ep, seed=f"{self.ep}fixed{self.fixn}{i}")
                f["img"][i] = path; self._urls = getattr(self, "_urls", {}); self._urls[i] = url; done = True
                if i not in f["anchors"]: f["anchors"].append(i)
            except Exception as e: log(f"repair of picture {i} failed: {e}", "WARN")
        redo = {i for i in (idx or []) if "vision_artifact" in codes and i < len(shots) and shots[i]["type"] == "kling" and i in f["clips"]}      # v8.3: a Kling clip the picture judge flagged is re-made (the old one is kept if the re-make fails)
        if "kling_short" in codes or redo:
            for i, s in enumerate(shots):
                if s["type"] != "kling" or (i in f["clips"] and i not in redo) or spent() >= cap_inr - 26: continue
                try:
                    self._urls = getattr(self, "_urls", None) or dict(f.get("urls") or {})
                    if i not in f["img"] or i in redo:          # v8.9.1: a picture that exists is animated as it is (its URL or the file), never re-bought just for a URL
                        path, url = M.still(shots[i].get("prompt") or units[i]["text"], os.path.join(self.out, f"img{i:03d}.jpg"), self.ep, seed=f"{self.ep}kfix{self.fixn}{i}"); f["img"][i] = path; self._urls = getattr(self, "_urls", {}); self._urls[i] = url
                    newp = M.animate(self._urls.get(i), f["img"][i], (s.get("motion") or "") + ". " + (s.get("prompt") or ""), os.path.join(self.out, f"clip{i:03d}" + (f"_r{self.fixn}" if i in redo else "") + ".mp4"), self.ep, hero=True)
                    f["clips"][i] = newp; done = True
                except Exception as e: log(f"repair of Kling clip {i} failed: {e}", "WARN")
        f["missing"] = [i for i in f["anchors"] if i not in f["img"]]
        f["delivered"] = {"kling": sum(1 for i, s in enumerate(shots) if s["type"] == "kling" and i in f["clips"]), "living": sum(1 for i, s in enumerate(shots) if s["type"] == "living" and i in f["clips"])}
        if done: self.fixn += 1; self.render_all()
        return max(0.0, spent())

def _render(job):
    """Segment boundaries = narration unit starts (the narration is the master clock). Long units are split into 2-3 shots (wide + detail) to keep a cut every
    ~5-7 s. v8.2: re-used pictures get their own crop (Director 'focus') and colour grade; the speaker tag and reaction effects are blended in by code; every
    segment is recorded in job.segmeta so a fix can re-render just a few of them."""
    files, shots, units, vo, out, ep = job.files, job.shots, job.units, job.vo, job.out, job.ep
    total = vo.duration; fps = RN.fps(); bounds = [0.0] + [u["start"] for u in units[1:]] + [total]
    segs, segmap, clean_map = [], {}, {}; prev_img = None; reuse = 0
    parts = []
    if S("SPEAKER_TAG_ON", bool) and FE.mode() != "classic":
        try:
            from whatifs.overlay import SpeakerTag
            ww, wh = RN.work_size(); tag = SpeakerTag(units, ww, wh, fps); parts.append(tag if tag.active() else None)
        except Exception as e: log(f"speaker tag skipped: {e}", "WARN")
    if S("CTA_ON", bool) and S("CTA_CHIP_ON", bool):
        try:
            from whatifs.overlay import CtaChip
            ww, wh = RN.work_size(); chip = CtaChip(units, ww, wh, fps)
            if chip.active(): parts.append(chip)
        except Exception as e: log(f"like/subscribe/share chip skipped: {e}", "WARN")
    if job.rx and S("REACTION_FX_ON", bool):
        try: ww, wh = RN.work_size(); parts.insert(0, RX.ReactionFX(job.rx, ww, wh, fps))        # reaction effects first, so the speaker tag is never zoomed
        except Exception as e: log(f"reaction effects skipped: {e}", "WARN")
    job.overlay = RX.Stack(parts) if any(parts) else None
    strong = set(ROOM.opening_units(units)) | set(RX.peak_units(units)); dyn = str(S("CAMERA_MOTION") or "dynamic").strip().lower() != "gentle"      # v8.9
    RN._LAST["move"] = None
    for i, u in enumerate(units):
        s = shots[i]; a, b = bounds[i], bounds[i + 1]; dur = b - a
        n_total = int(round(b * fps)) - int(round(a * fps))
        if n_total <= 0: continue
        own = files["img"].get(i); img = own or prev_img
        reuse = 0 if own else reuse + 1
        if own: prev_img = own
        pieces = 1 if dur < 7.5 or s["type"] in ("graphic",) else (2 if dur < 13 else 3)
        cut = [int(n_total * k / pieces) for k in range(pieces + 1)]
        cd = 0.0
        if i in files["clips"] and s["type"] in ("kling", "living"):
            try: cd = RN.probe_dur(files["clips"][i])
            except Exception: cd = 0.0
        if cd > 0 and dur > cd * 1.25 and s["type"] != "graphic":       # v8.3: a clip plays at its own speed; the rest of a longer line is a camera move on the same picture (no frame-doubling judder)
            n0 = min(n_total - 1, max(1, int(round(cd * fps)))); rest = n_total - n0; extra = 1 if (rest / fps) < 7.5 else 2
            cut = [0, n0] + [n0 + int(rest * j / extra) for j in range(1, extra + 1)]; pieces = len(cut) - 1
        for k in range(pieces):
            nf = cut[k + 1] - cut[k]; p = os.path.join(out, f"seg{i:03d}_{k}.mp4"); f0 = int(round(a * fps)) + cut[k]
            RN.set_overlay(job.overlay); RN.set_cursor(f0)
            def draw(path, ovl):
                RN.set_overlay(ovl); RN.set_cursor(f0)
                if k == 0 and i in files["clips"]: RN.clip_segment(files["clips"][i], path, nf, loop=s["type"] == "stock", push=(0.07 if i in strong else 0.035) if (s["type"] == "living" and dyn) else 0.0)
                elif s["type"] == "graphic" and k == 0: RN.graphic_segment(s.get("graphic") or {}, img, path, nf)
                elif img:
                    RN.parallax_segment(img, path, nf, seed=f"{ep}{i}{k}", detail=((k + reuse) % 2 == 1), focus=s.get("focus"), look=None if own else RN.LOOKS[reuse % len(RN.LOOKS)], energy="high" if (i in strong and k == 0) else "calm",
                                       move=s.get("camera") if k == 0 else None)      # v8.9: the Director's suggested move (validated in render.pick_move)
                else: RN.graphic_segment({"label": "", "from": 0, "to": 0}, None, path, nf)
            try: draw(p, job.overlay)
            except Exception as e:
                log(f"segment {i}.{k} failed: {e} -> fallback", "WARN")
                RN.set_overlay(job.overlay); RN.set_cursor(f0); RN.graphic_segment({"label": "", "from": 0, "to": 0}, img, p, nf)
            segs.append(p); job.segmeta.append({"path": p, "i": i, "k": k, "f0": f0, "nf": nf, "img": img})
            if k == 0:
                segmap[i] = p
                if i in job.reel_shots and job.overlay is not None:     # v8.3: reels get a clean copy of EVERY reel shot (no speaker chip, no reaction burst, nothing half-cropped by the 9:16 cut)
                    cp = os.path.join(out, f"clean{i:03d}.mp4")
                    try: draw(cp, None); clean_map[i] = cp
                    except Exception as e: log(f"clean copy of segment {i} skipped: {e}", "WARN")
    RN.set_overlay(None)
    files["segments"] = {i: clean_map.get(i, segmap.get(i, segs[0])) for i in range(len(shots))}
    job.video = RN.concat(segs, os.path.join(out, "video.mp4"))
    events = []
    for i, s in enumerate(shots):
        if s["type"] == "kling": events.append(("boom", units[i]["start"])); events.append(("riser", units[i]["start"]))
        elif units[i]["tag"] == "reveal": events.append(("whoosh", max(0, units[i]["start"] - 0.3)))
    if job.rx and S("REACTION_FX_ON", bool): events += RX.sfx_events(job.rx)
    job.events = events; files["events"] = events
    job.design = SD.design(shots, units, total, getattr(job, "rhythm", None), seed=ep) if S("SOUND_DESIGN_ON", bool) else None
    mix = RN.score(total, ep, events, vo.wav_path, design=job.design)
    aud = RN.write_mix(mix, os.path.join(out, "mix.wav"))
    return RN.mux(job.video, aud, os.path.join(out, "master.mp4"))



# =====================================================================================================================================
# v8.9: living-still motion prompts and the pre-spend plan check
# =====================================================================================================================================
def motion_prompt(shot, line="", opening=False):
    """The prompt sent to the image-to-video model. Kling clips: unchanged (motion + prompt). Living stills: the same count and model, but the motion is
    atmospheric and alive (fog, embers, ripples, dust in god rays, chosen from what the shot shows) and stronger inside the opening window."""
    base = (shot.get("motion") or "") + ". " + (shot.get("prompt") or "")
    if shot.get("type") != "living": return base
    from whatifs.data import ATMOS, ATMOS_DEFAULT, LIVING_MOTION
    txt = (str(line) + " " + str(shot.get("prompt") or "")).lower()
    atm = next((a for rx, a in ATMOS if re.search(rx, txt)), ATMOS_DEFAULT)
    return f"{LIVING_MOTION['opening' if opening else 'calm']}, {atm}. {shot.get('prompt') or line}"

def plan_check(S_, units):
    """v8.9 preventive check, FREE, right before the first paid picture. Repairs what it safely can (missing prompts, the style lock, Kling / living counts
    above the plan, a missing title) and logs it; stops ONLY for what cannot be repaired (no shots, or narration under the floor), so no money is ever
    spent on a plan that would fail final QC anyway. The counts are never raised (budget rules unchanged)."""
    shots = [dict(x) for x in S_.get("shots") or []]; plan = S_.get("plan") or {}; fixes = []
    if not shots: raise RuntimeError("plan check: the shot list is empty - nothing spent; will retry")
    floor = 20 if SMALL else S("RUNTIME_MIN_SEC", int) + 3
    if float((S_.get("vo") or {}).get("duration") or 0) < floor: raise RuntimeError("plan check: narration under the floor - nothing spent; will retry")
    if len(shots) != len(units): fixes.append(f"{len(shots)} shots for {len(units)} lines (extra dropped, missing lines get a still)")
    shots = (shots + [{"type": "still", "prompt": u["text"], "unit": i} for i, u in enumerate(units)][len(shots):])[:len(units)]
    lock = str(S("STYLE_LOCK") or "").strip()
    for i, x in enumerate(shots):
        if x.get("type") in ("still", "living", "kling"):
            if not str(x.get("prompt") or "").strip(): x["prompt"] = units[i]["text"]; fixes.append(f"shot {i} had no prompt")
            if lock and lock not in x["prompt"]: x["prompt"] = x["prompt"].rstrip(". ") + ". " + lock
    for typ in ("kling", "living"):
        idx = [i for i, x in enumerate(shots) if x.get("type") == typ]; cap = int(plan.get(typ) or 0)
        for i in idx[cap:]: shots[i]["type"] = "still"; fixes.append(f"{typ} on shot {i} above the plan -> still")
    pkg = S_.get("pkg") or {}
    if not [t for t in pkg.get("titles") or [] if str(t).strip()]:
        t = ((S_.get("d") or {}).get("promise") or {}).get("title") or ((S_.get("room") or {}).get("spine") or {}).get("headline")
        if t: pkg["titles"] = [t]; S_["pkg"] = pkg; fixes.append("no title from the Packager -> the promise title")
    if fixes: log(f"plan check: {len(fixes)} repair(s) before any money: {'; '.join(fixes[:6])}", "WARN")
    S_["shots"] = shots; S_["plan_check"] = {"repairs": len(fixes)}
    return S_

_TAKEN = ("PLANNING", "VOICING", "VISUALS", "UPLOADED", "SCHEDULED", "LIVE1", "LIVE", "HELD", "HOLD_QC", "STUCK_PRIVATE")
def _slot_taken(st, slot_iso):
    """v8.3: one episode per slot. Two ticks close together (or a manual 'Run workflow') used to make two videos for the same slot and pay twice."""
    return next((e for e in st.rows("Episodes") if e.get("slot_et") == slot_iso and e.get("status") in _TAKEN), None)

def _cleanup_work(out):
    """v8.3: delete the big intermediate files (segments, clean copies, reel parts, joined video) once an episode is finished or held. Master, reels, art and checkpoints stay."""
    try:
        for f in os.listdir(out):
            if re.match(r"(seg\d+_\d+|clean\d+|r\d_[\w]+|video)\.(mp4|txt)$", f) or f.endswith((".raw.wav", ".mp4.txt")):
                try: os.remove(os.path.join(out, f))
                except OSError: pass
    except OSError: pass

def produce(slot_iso, episode_id=None, eps_left=None, fix=False):
    st = store()
    if not fix and episode_id is None:
        t = _slot_taken(st, slot_iso)
        if t:
            log(f"slot {slot_iso} already has {t['episode_id']} ({t.get('status')}) - not producing a second video for it (nothing spent)", "WARN")
            return {"ok": False, "skipped": "slot_taken", "episode": t["episode_id"]}
    if not fix and S("PREFLIGHT_ON", bool):
        ok, why = PF.check()
        if not ok:
            log(f"pre-flight failed: {why} - not starting (nothing spent)", "ERROR"); _preflight_mail(why)
            return {"ok": False, "skipped": "preflight", "why": why}
    prev = None
    if fix: prev = next((e for e in st.rows("Episodes") if e["episode_id"] == episode_id), None)
    elif episode_id is None: prev = _resumable(slot_iso)
    ep = episode_id or (prev["episode_id"] if prev else "EP" + now_utc().strftime("%Y%m%d%H%M"))
    JOB["episode"] = ep; out = os.path.join(WORK, ep); os.makedirs(out, exist_ok=True)
    try: refresh_spend()           # v8.3: spend made by other jobs since this one started counts before any new paid step
    except Exception as e: log(f"spend refresh skipped: {scrub(e)}", "WARN")
    if prev: st.update("Episodes", "episode_id", ep, {"status": "PLANNING", "slot_et": slot_iso, "notes": CK.set_attempts(prev.get("notes"), CK.attempts(prev) + 1), "updated": iso()})
    else: st.append("Episodes", [{"episode_id": ep, "slot_et": slot_iso, "status": "PLANNING", "notes": "attempts=1", "updated": iso()}])
    try:
        stage = CK.restore(ep, out) if prev else None
        if fix and not stage: raise RuntimeError("no saved checkpoint for this held video (checkpoints are kept in your Drive; they may have been deleted)")
        if stage:
            S_ = json.load(open(os.path.join(out, "plan.json")))
            log(f"resuming from the saved '{stage}' checkpoint: the AI writing is not paid for again" + (" and neither are the saved pictures and clips" if stage != "plan" else ""))
            if not fal_allowed(): raise RuntimeError("image credit is empty or the monthly cap is reached - nothing more will be spent; will retry next hour")
        else:
            if not fal_allowed(): raise RuntimeError("image credit is empty - top up fal.ai (reminder email sent); will retry next hour")
            S_ = _stage_plan(ep, out, eps_left, slot_iso); CK.save(out, ep, "plan", {"plan.json": S_})
            consume_tease(S_)              # v8.9.1: the teased premise is used up only now that the plan (which made it) is safely saved
        d, plan, shots = S_["d"], S_["plan"], S_["shots"]
        vo = _vo_of(S_, out); tl = json.load(open(vo.timeline_path)); units = tl["units"]
        S_ = plan_check(S_, units); shots = S_["shots"]          # v8.9: the last free check before any picture money is spent
        st.update("Episodes", "episode_id", ep, {"status": "VISUALS", "updated": iso()})
        # ---- assets (only what is missing is made on a resume)
        have = _load_assets(out) if stage in ("assets", "hold") else None
        try: refresh_spend()
        except Exception: pass
        files = _assets(shots, units, out, ep, budget=d["stills"] + plan["living"] + plan["kling"], have=have)
        need_img = files["anchors"]; miss = [i for i in need_img if i not in files["img"]]
        log(f"images: {len(files['img'])} for {len(shots)} shots (budget {d['stills'] + plan['living'] + plan['kling']}, Kling delivered {files['delivered']['kling']}/{plan['kling']})")
        if need_img and len(miss) / len(need_img) > 0.15:
            CK.save(out, ep, "assets", {"assets.json": _assets_state(files)})        # keep what was made: the retry only makes the rest
            raise RuntimeError(f"{len(miss)} of {len(need_img)} images failed - not publishing a weak video; will retry (the pictures that worked are saved)")
        if stage not in ("assets", "hold") or (have and len(files["img"]) + len(files["clips"]) > len(have["img"]) + len(have["clips"])):
            CK.save(out, ep, "assets", {"assets.json": _assets_state(files)})
        res = _finish(st, ep, out, S_, files, vo, tl, units, fix, slot_iso, stage)
        _cleanup_work(out)
        return res
    except Exception as e:
        log(f"episode failed: {e}", "ERROR"); st.update("Episodes", "episode_id", ep, {"status": "FAILED", "notes": CK.set_attempts(str(e)[:360], CK.attempts(next((r for r in st.rows("Episodes") if r["episode_id"] == ep), {}))), "updated": iso()})
        raise
    finally: flush_log()

def _finish(st, ep, out, S_, files, vo, tl, units, fix, slot_iso, stage):
    d, room, shots, pkg, rplans, chs, hook_rec = S_["d"], S_["room"], S_["shots"], tidy_pkg(S_["pkg"]), S_["rplans"], S_["chs"], S_["hook_rec"]
    rx = RX.find_events(units) if (FE.mode() != "classic" and S("REACTION_FX_ON", bool)) else []
    job = Job(ep=ep, out=out, files=files, shots=shots, units=units, vo=vo, tl=tl, rx=rx, fps=RN.fps(), srt=os.path.join(out, "captions.srt"), overlay=None, rhythm=d.get("rhythm_plan") or {},
              reel_shots={int(i) for rp in rplans[:4] for i in rp.get("shots", [])})
    master = job.render_all(); RN.srt(tl, job.srt)
    # ---- packaging art: reuse on a one-click fix; a weak thumbnail is first redrawn from the same key art (free) and only then re-made (paid)
    have_art = fix and os.path.exists(os.path.join(out, "thumb.jpg"))
    if have_art: thumb = os.path.join(out, "thumb.jpg"); thumb_master = thumb; phone = ART.phone_check(Image.open(thumb))
    else: thumb, thumb_master, phone = ART.thumbnail(pkg.get("thumb_prompt", room["spine"]["premise"]), pkg.get("thumb_text", ""), out, ep)
    okt, tinfo = QC.check_thumb(thumb, phone)
    for boost in (1, 2):
        if okt or have_art: break
        log(f"thumbnail weak {tinfo}: redrawing the same key art with stronger contrast (free, try {boost})", "WARN")
        thumb, thumb_master, phone = ART.recompose(out, pkg.get("thumb_text", ""), boost); okt, tinfo = QC.check_thumb(thumb, phone)
    if not okt and not have_art:
        log(f"thumbnail still weak {tinfo}, making new key art once", "WARN")
        thumb, thumb_master, phone = ART.thumbnail(pkg.get("thumb_prompt", "") + ", higher contrast, brighter subject", pkg.get("thumb_text", ""), out, ep + "b")
    thumb_b = _thumb_b(pkg, room, out, ep, fix)          # v8.5 packaging rescue: a runner-up thumbnail with a DIFFERENT idea, used only if the video lags
    covers = []
    for k, (p, t) in enumerate(zip((pkg.get("reel_cover_prompts") or ["", ""])[:2], (pkg.get("reel_cover_texts") or ["", ""])[:2])):
        cp = os.path.join(out, f"cover{k}.jpg"); covers.append(cp if (fix and os.path.exists(cp)) else ART.reel_cover(p, t, out, ep, k))
    for k in range(len(covers), len(rplans[:4])):         # v8.5: reels 3-4 get a FREE cover drawn from their own opening picture + hook text
        cp = os.path.join(out, f"cover{k}.jpg")
        if not (fix and os.path.exists(cp)):
            try: cp = ART.reel_cover_free(_reel_src_image(files, rplans[k], thumb_master), rplans[k].get("hook_text", ""), out, k)
            except Exception as e: log(f"free cover {k} failed ({e}) - using the thumbnail art", "WARN"); cp = thumb_master
        covers.append(cp)
    reel_files = []
    for k, rp in enumerate(rplans[:4]):
        try:
            cov = covers[k] if k < len(covers) else thumb_master; rf = os.path.join(out, f"reel{k}.mp4")
            if fix and os.path.exists(rf): rd_ = RN.probe_dur(rf)
            else: rf, rd_ = REELS.build_reel(k, rp, files["segments"], cov, blend(), "urgent", out, speaker_blends=speaker_blends(d.get("guest")))
            ok, info = QC.check_video(rf, rd_, vertical=True, tol=1.0)
            if ok: reel_files.append((rf, rp, cov))
            else: log(f"reel {k} failed QC {info}", "WARN")
        except Exception as e: log(f"reel {k} failed: {e}", "WARN")
    # ---- final QC of the long video: full check, free fixes, small capped paid fixes; anything left = HOLD (never uploaded)
    chk = QC.full_check(job.qc_ctx()); notes = []
    for wait in (90, 240):          # v8.3: if the ONLY problem is that the independent picture judge was unreachable, give it time to come back before holding
        if chk["ok"] or not all(p["code"] == "vision_unavailable" for p in chk["problems"]): break
        log(f"picture judge unreachable - waiting {wait}s and asking again", "WARN"); time.sleep(wait); chk = QC.full_check(job.qc_ctx())
    log(f"QC long video: {'PASS' if chk['ok'] else 'problems: ' + '; '.join(p['code'] for p in chk['problems'])} | {chk['info']}")
    if not chk["ok"]:
        cap = S("FIX_MAX_PAID_INR", float) if fix else S("AUTO_FIX_PAID_INR", float)
        chk, notes, spent = FIX.auto_fix(job, chk, cap, lambda: QC.full_check(job.qc_ctx()))
        master = job.master; log(f"QC after fixes: {'PASS' if chk['ok'] else 'still failing: ' + '; '.join(p['code'] for p in chk['problems'])} (fixes: {', '.join(notes) or 'none'}; paid Rs {spent:.0f})")
    if not chk["ok"] and S("HOLD_ON_QC_FAIL", bool): return _hold(st, ep, out, chk, notes, fix)
    if not chk["ok"]: log("QC failed but HOLD_ON_QC_FAIL is FALSE - uploading anyway (not recommended)", "ERROR")
    RX.record(ep, rx, (d.get("strategies") or {}).get("banter", ""), total_sec=vo.duration)
    cut_map, _ = CUTMAP.run_cutmap(out, vo.wav_path, tl, master, RN.fps(), files.get("events", []), ep, master_duration=RN.probe_dur(master))
    srt = job.srt
    title = (pkg.get("titles") or [room["spine"].get("headline") or room["spine"].get("title_candidates", ["What If?"])[0]])[0]
    nxt = None
    if S("NEXT_LINK_ON", bool):                           # v8.7: send viewers on to the best related earlier video (sessions + returning viewers)
        try: nxt = GR.related_episode(st.rows("Episodes"), st.rows("Analytics"), d.get("family") or "", ep)
        except Exception as e: log(f"next-video link skipped: {scrub(e)}", "WARN")
    desc = _description(pkg.get("description", ""), chs, room, ep, nxt)
    if fix: slot_iso = _fix_slot(slot_iso)
    vid = PUB.yt_upload(master, title, desc, pkg.get("tags", []), publish_at=slot_iso, ai_label=S("AI_LABEL_DEFAULT", bool))
    st.update("Episodes", "episode_id", ep, {"title": title, "yt_id": vid, "slot_et": slot_iso, "status": "UPLOADED", "updated": iso()})   # recorded at once: no double upload
    try:
        PUB.yt_thumbnail(vid, thumb); PUB.yt_captions(vid, srt); PUB.yt_playlist(vid, _playlist(d.get("family") or d["ptype"]))
        rel = {"title": title, "pinned": pkg.get("pinned_comment", "") + (f"\n\nWatch next: {nxt['title']} {nxt['url']}" if nxt else ""), "reels": [],
               "title_b": _title_b(pkg, title), "thumb_b": os.path.basename(thumb_b) if thumb_b else ""}
        for k, (rf, rp, cov) in enumerate(reel_files):
            rel["reels"].append({"file": rf, "cover": cov, "caption": rp.get("caption", ""), "hook": rp.get("hook_text", ""), "format": rp.get("format")})
        json.dump(rel, open(os.path.join(out, "release.json"), "w"))
        assets = _persist(out, ep); assets.update(_archive(out, ep, master, srt)); assets.update(_review_files(out, ep))
        cur = next((r for r in st.rows("Episodes") if r["episode_id"] == ep), {}); old = CK._assets_of(cur)
        deg = take_degraded() if S("DEGRADED_NOTE_ON", bool) else []
        st.update("Episodes", "episode_id", ep, {"title": title, "yt_id": vid, "status": "SCHEDULED", "release_tag": ep, "assets": dict({k: v for k, v in old.items() if k.startswith("_ckpt")}, **assets), "updated": iso(),
                                               "cost_inr": round(_ep_cost(ep), 1), "notes": CK.set_attempts(("degraded: " + "; ".join(deg))[:300] if deg else "", CK.attempts(cur))})
    except Exception as e:
        try: PUB.yt_set_privacy(vid, "private")          # uploaded but not finished: keep it private so a half-packaged video never publishes on its own
        except Exception as x: log(f"could not make {vid} private: {x}", "WARN")
        raise
    CK.clear(ep)
    nt = d.get("next_tease") or {}
    if nt.get("premise") and S("NEXT_TEASE_ON", bool):          # v8.9: only a video that is really going out sets the promise the next episode keeps
        set_setting("NEXT_PREMISE", json.dumps(dict({k: nt.get(k, "") for k in ("premise", "headline", "family", "ptype")}, set_at=iso()), ensure_ascii=False)[:600])
    log(f"SCHEDULED {vid} for {slot_iso}: {title}", public=f"SCHEDULED {vid} for {slot_iso}")
    if not S("PILOT_DONE", bool): set_setting("PILOT_DONE", "TRUE"); log("pilot episode made")
    PUB.email("Video scheduled", f"<p>{title}<br>Goes live {slot_iso} (UTC). To stop it, type KILL in the Episodes tab, kill column.</p>"
              f"<p>{_review_note(hook_rec, cut_map)}</p>", kind="info")
    return {"ok": True, "episode": ep, "yt": vid, "master": master, "reels": [r[0] for r in reel_files], "thumb": thumb, "title": title, "qc_fixes": notes}

def tidy_pkg(pkg):
    """v8.6: code-checked packaging (idempotent, also applied to plans saved by older versions): titles re-ordered so a clean one (30-60 characters,
    not shouting, not repeating the thumbnail words) comes first and a clean runner-up second; thumbnail texts cut to THUMB_MAX_WORDS words."""
    pkg = dict(pkg or {})
    for k in ("thumb_text", "thumb_text_b"):
        if pkg.get(k): pkg[k] = GR.thumb_words(pkg[k])
    titles = [t for t in (pkg.get("titles") or []) if str(t or "").strip()]
    if titles:
        best, runner = GR.choose_titles(titles, pkg.get("thumb_text", ""))
        rest = [t for t in titles if str(t).strip().lower() not in (best.lower(), runner.lower())]
        pkg["titles"] = [best] + ([runner] if runner else []) + rest
    return pkg

def _title_b(pkg, title):
    """v8.5: the Packager's runner-up title (its list is best-first), if it differs from the one used."""
    for t in (pkg.get("titles") or [])[1:]:
        t = str(t or "").strip()
        if t and t.lower() != str(title).strip().lower(): return t
    return ""

def _thumb_b(pkg, room, out, ep, fix):
    """v8.5: the B thumbnail (one premium image, about Rs 8). It must be a DIFFERENT idea, not a re-roll; any failure just means no rescue for this video."""
    if not S("PKG_RESCUE_ON", bool): return ""
    p = os.path.join(out, "thumb_b.jpg")
    if fix and os.path.exists(p): return p
    prompt, text = str(pkg.get("thumb_prompt_b") or "").strip(), str(pkg.get("thumb_text_b") or "").strip()
    if not prompt: return ""
    try:
        import shutil
        b_dir = os.path.join(out, "_b"); txt = text or pkg.get("thumb_text", "")
        up_b, _, phone = ART.thumbnail(prompt, txt, b_dir, ep + "B", side="right")
        ok, info = QC.check_thumb(up_b, phone)
        if not ok:                                   # v8.6: the B thumbnail passes the same phone-size check as the main one (free redraws), or is not used
            for boost in (1, 2):
                up_b, _, phone = ART.recompose(b_dir, txt, boost, side="right"); ok, info = QC.check_thumb(up_b, phone)
                if ok: break
        if not ok: log(f"B thumbnail failed the phone-size check {info} - no rescue package for this video", "WARN"); return ""
        shutil.copyfile(up_b, p); return p          # the upload-sized copy (YouTube's 2 MB thumbnail limit)
    except Exception as e: log(f"B thumbnail skipped: {e}", "WARN"); return ""

def _reel_src_image(files, rp, fallback):
    """The first reel shot that has its own picture (for a free cover)."""
    for i in rp.get("shots", []):
        pth = files.get("img", {}).get(int(i)) or files.get("img", {}).get(str(i))
        if pth and os.path.exists(pth): return pth
    return fallback

def _fix_link(ep):
    from urllib.parse import quote
    repo = env("GH_REPO")
    if not repo: return ""
    return f"https://github.com/{repo}/issues/new?title={quote('FIX ' + ep)}&body={quote('Click Submit new issue. A robot fixes the held video and schedules it.')}"

def _hold(st, ep, out, chk, notes, fix):
    """Final QC still failing: nothing is uploaded. The re-render bundle is saved to Drive, you get ONE email with a fix link, new episodes are paused until you act."""
    CK.save(out, ep, "hold")
    probs = "; ".join(f"{p['code']}: {p['detail']}" for p in chk["problems"])[:380]
    st.update("Episodes", "episode_id", ep, {"status": "HOLD_QC", "notes": CK.set_attempts("QC hold: " + probs, 1), "updated": iso()})
    link = _fix_link(ep)
    items = "".join(f"<li><b>{p['code']}</b>: {p['detail']}</li>" for p in chk["problems"]) + "".join(f"<li>degraded: {x}</li>" for x in take_degraded())
    act = (f"<p><a href='{link}'>Click here, then press the green <b>Submit new issue</b> button</a>. A robot repairs the video "
           "(re-makes failed pictures within a Rs " + str(int(S('FIX_MAX_PAID_INR', float))) + " limit), checks it again, and schedules it only if it passes.</p>") if link else \
          "<p>Open GitHub, Actions, 'Fix held video', and run it with this episode id.</p>"
    PUB.email("Video held: the final check failed (one click to fix)" if not fix else "Fix attempt failed: video still held",
              f"<p>Episode <b>{ep}</b> was NOT uploaded.</p><ul>{items}</ul><p>Already tried automatically: {', '.join(notes) or 'nothing applied'}.</p>{act}"
              "<p>To drop this video instead, type KILL in its kill cell in the Episodes tab. New videos wait until you decide.</p>")
    return {"ok": False, "held": True, "episode": ep, "problems": [p["code"] for p in chk["problems"]]}

def _fix_slot(slot_iso):
    """Keep the original slot if it is still ahead; else the next free slot."""
    from whatifs.core import parse_iso
    from whatifs import manage as MG
    t = parse_iso(slot_iso)
    if t and t > now_utc() + dt.timedelta(minutes=50): return slot_iso
    taken = {e.get("slot_et") for e in store().rows("Episodes") if e.get("status") in ("SCHEDULED", "LIVE1", "LIVE", "HELD")}
    return next((s.strftime("%Y-%m-%dT%H:%M:%SZ") for s in MG.next_slots(12, now_utc() + dt.timedelta(minutes=50)) if s.strftime("%Y-%m-%dT%H:%M:%SZ") not in taken), slot_iso)

def fix_held(ep):
    """The one-click fix (GitHub issue 'FIX <episode>'): restore the held video's bundle, repair, re-check, upload only if it now passes."""
    st = store(); row = next((e for e in st.rows("Episodes") if e["episode_id"] == ep), None)
    if not row or row.get("status") != "HOLD_QC": raise RuntimeError(f"{ep} is not a held video (status: {row.get('status') if row else 'unknown'})")
    return produce(row.get("slot_et"), episode_id=ep, fix=True)

def _save_hook_final(rec, out):
    try: json.dump(rec, open(os.path.join(out, "hooks.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    except Exception as e: log(f"could not update hooks.json: {scrub(e)}", "WARN")

def _review_note(hook_rec, cut_map):
    """One plain sentence for the owner: what to look at before the slot. Counts only; no hook text or topic in the email log."""
    bits = []
    if hook_rec and hook_rec.get("candidates"):
        bits.append(f"Opening hooks: {len(hook_rec['candidates'])} scored candidates saved (status: {hook_rec.get('status')}) in the Hook_Candidates tab.")
    if cut_map:
        s = cut_map["summary"]; bits.append(f"Cut map ({cut_map['method']}{', estimate' if cut_map.get('estimate') else ''}): {s['trim_suggested']} suggested trim(s), {s['review_only']} review-only, in the Cut_Map tab. Nothing was cut automatically.")
    return " ".join(bits) or "No hook or cut-map report was produced for this episode."

def _review_files(out, ep):
    """Private Drive copies of the per-episode review reports (hooks, cut map). Keys start with '_' so the reel release code ignores them."""
    if FAKE or not S("REVIEW_TO_DRIVE", bool): return {}
    ids = {}
    for f in ("hooks.json", "cutmap.json", "cutmap.md", "table_read.json"):
        p = os.path.join(out, f)
        if os.path.exists(p):
            try: ids["_review_" + f] = PUB.drive_upload(p, f"{ep}_{f}", public=False)[0]
            except Exception as e: log(f"review upload failed for {f}: {e}", "WARN")
    return ids

def _strip_beats(script):
    lines, marks = [], []
    for raw in script.splitlines():
        if raw.strip().startswith("##"):
            marks.append(len([l for l in lines if l.strip() and not l.strip().startswith("[pause")])); continue
        lines.append(raw)
    clean = "\n".join(lines)
    return clean, marks

def _description(desc, chs, room, ep="", nxt=None):
    chapters = "\n".join(f"{t} {n}" for t, n in chs) if len(chs) >= 3 else ""
    if "Chapters" in desc: body = desc.replace("Chapters", "Chapters\n" + chapters if chapters else "")
    else: body = desc + (("\n\nChapters\n" + chapters) if chapters else "")      # v8.3: chapters are added even if the packager forgot the word 'Chapters'
    if nxt:                                                  # v8.7: right after the hook paragraph, where it is seen without 'more'
        parts = body.split("\n\n", 1); body = parts[0] + f"\n\nWatch next: {nxt['title']} {nxt['url']}" + ("\n\n" + parts[1] if len(parts) > 1 else "")
    foot = ""
    if S("CTA_ON", bool) and S("CTA_DESC_ON", bool):
        try:
            link = ""
            try: link = f"https://www.youtube.com/channel/{PUB.yt_channel().get('id')}?sub_confirmation=1" if not FAKE else ""
            except Exception: link = ""
            foot = CTA.description_footer(ep or room.get("spine", {}).get("premise", ""), link)
        except Exception as e: log(f"description footer skipped: {scrub(e)}", "WARN")
    return body + (("\n\n" + foot) if foot else "") + "\n\nThis video uses AI-assisted visuals and narration over an original script. Science is simplified for storytelling."

def _playlist(ptype):
    from whatifs.data import FAMILY_PLAYLIST
    if ptype in FAMILY_PLAYLIST: return FAMILY_PLAYLIST[ptype]
    return {"cosmic": "What If: Space", "body": "What If: Your Body", "collective": "What If: Everyone On Earth"}.get(ptype, "What If")

def _mark_premise(premise, ep):
    st = store()
    for r in st.rows("Premises"):
        if r["premise"].lower() == premise.lower():
            st.update("Premises", "premise_id", r["premise_id"], {"status": "USED", "episode_id": ep, "used_at": iso()}); return
    st.append("Premises", [{"premise_id": "N" + ep, "grid": "N", "premise": premise, "status": "USED", "episode_id": ep, "used_at": iso()}])
    st.append("Banned", [{"phrase": premise.lower()[:80], "reason": "already made"}])

def _ep_cost(ep):
    t = 0.0
    for r in store().rows("Cost_Log"):
        if r.get("episode_id") == ep:
            try: t += float(r["inr"])
            except Exception: pass
    return t

def _archive(out, ep, master, srt_path):
    """DRIVE_ARCHIVE: copy the finished master + captions to your private Drive; keep only the newest DRIVE_ARCHIVE_KEEP masters."""
    if FAKE or not S("DRIVE_ARCHIVE", bool): return {}
    ids = {}
    for key, path in (("_master.mp4", master), ("_captions.srt", srt_path)):
        try: ids[key] = PUB.drive_upload(path, f"{ep}{key}", public=False)[0]
        except Exception as e: log(f"archive failed for {key}: {e}", "WARN")
    try:
        keep = S("DRIVE_ARCHIVE_KEEP", int); st = store()
        old = [e for e in st.rows("Episodes") if e.get("episode_id") != ep and "_master.mp4" in str(e.get("assets", ""))]
        for e in old[:max(0, len(old) - max(0, keep - 1))]:
            a = json.loads(e.get("assets") or "{}"); fid = a.pop("_master.mp4", None)
            if fid: PUB.drive_delete(fid); st.update("Episodes", "episode_id", e["episode_id"], {"assets": a})
    except Exception as e: log(f"archive clean-up skipped: {e}", "WARN")
    return ids

def _persist(out, ep):
    """Keep reels + covers + release info in YOUR PRIVATE Google Drive until release (never public before launch)."""
    if FAKE: return {}
    ids = {}
    for f in sorted(os.listdir(out)):
        if re.match(r"(reel\d\.mp4|cover\d\.jpg|thumb_b\.jpg|release\.json)$", f):
            try: ids[f] = PUB.drive_upload(os.path.join(out, f), f"{ep}_{f}", public=False)[0]
            except Exception as e: log(f"drive save failed for {f}: {e}", "WARN")
    return ids


