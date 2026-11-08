"""v10 Specials (K134; owner request 2026-11-08): short (~15 s) cast reels that are NOT episode cut-downs.
- 'cast_intro' (one time, the channel's launch reel): a cinematic dramatic entrance of the three cast members (about 3 s each, in their signature
  look and pride), a courtroom-doors teaser and an end card that points to the YouTube and Instagram profiles. Written here, no AI writing call.
- 'special' (SPECIALS_DAYS, twice a month): one witty in-world micro-story with the same cast (concept picked from IDEAS by one Sonnet call).
Pictures: the cast's LOCKED character-sheet portraits animated by the hero video model (Kling, fal); a missing portrait is drawn first.
Text, cards and sound are made by code (₹0); the end card always carries the subscribe line. Original cast and scenes only (K99): techniques
from technique cards, never copied scenes or third-party characters.
Money: each reel <= SPECIAL_REEL_CAP_INR; all specials in a month <= SPECIALS_EARMARK_INR (owner's +₹300, kept out of production)."""
from __future__ import annotations
import hashlib, json, os, subprocess
import numpy as np
from whatifs.core import S, log, store, iso, now_utc, parse_iso, FAKE, WORK, scrub, SMALL

LOOK_SUFFIX = "cinematic, dramatic rim light, shallow depth of field, rich film colour, vertical 9:16 framing, no text"
CAST_INTRO = [
    {"who": "VALE", "sec": 3.0, "motion": "slow push-in, he lifts a worn evidence notebook toward the camera and gives a knowing half-smile, rain-lit city glow behind, dust in the light",
     "card": "INSPECTOR VALE", "line": "finds the flaw in reality"},
    {"who": "GRIMM", "sec": 3.0, "motion": "he turns sharply to camera from a chalkboard of equations, raises one eyebrow, claps once, sparks from a coil behind him",
     "card": "DR. GRIMM", "line": "objects to everything. Even gravity."},
    {"who": "ROSA", "sec": 3.0, "motion": "she sips from a floral teacup, sets it down, lifts a wooden gavel, unimpressed smile, warm courtroom lamps",
     "card": "NANA ROSA", "line": "presiding. Tea first."},
    {"who": "SET", "sec": 3.5, "motion": "tall courtroom doors swing open toward the camera, golden light floods in, dust swirls, camera glides forward",
     "card": "REALITY ON TRIAL", "line": "Court opens Tuesday. You're the jury."},
]
# ---------------------------------------------------------------- the Character Love Engine (owner 2026-11-08)
# Renewable formats (weights are learned from each format's engaged views at 7 days, with an exploration floor); lore drops are rationed.
FORMATS = {
    "lab_log":    {"w": 3, "who": "GRIMM", "brief": "Grimm's Lab Log #{n}: one gloriously doomed experiment in his gothic lab (bubbling flasks, coloured fumes, sparks), PG, ends in a comic fizzle and his grudging wonder"},
    "tea_ruling": {"w": 3, "who": "ROSA", "brief": "Nana's Tea Ruling: she settles one everyday dispute (from the comments when given) with one dry sentence, Vale and Grimm reacting"},
    "deduction":  {"w": 2, "who": "VALE", "brief": "Vale's 15-second deduction: he deduces something harmless and charming about the viewer, three fingers, the third one turns it"},
    "rivalry":    {"w": 2, "who": "VALE", "brief": "Vale and Grimm, former lab partners: a small rivalry that ends in a hidden kindness"},
    "vote":       {"w": 2, "who": "ROSA", "brief": "the jury decides: show the outcome the comments chose last time, then open a new two-option vote for the comments"},
    "backstory":  {"w": 1, "who": "ROSA", "brief": "a short, bittersweet lore drop from the CANON (one fact), then the other two show they are family; warm, earned, never tragic detail"},
}
CANON = [
    ("ROSA", "At nine, everyone told her a girl couldn't do physics; she kept the chipped teacup she was holding when she proved them wrong."),
    ("ROSA", "She has known Vale and Grimm since they were students who set the lab on fire twice."),
    ("GRIMM", "Grimm was Vale's lab partner; he quit the day an experiment proved him wrong, and he still keeps the notebook."),
    ("GRIMM", "Once an episode his mask slips: a moment of real wonder he hides at once."),
    ("VALE", "Vale lists three facts on his fingers because his first teacher made him count his evidence out loud."),
    ("VALE", "Vale's grey overcoat belonged to the detective who believed him when nobody else did."),
]
ASKS = {
    "identity": "Take your seat on the jury. Subscribe.",
    "beaker": "Every subscriber funds one beaker. Grimm needs many beakers.",
    "nana": "Nana says subscribe. Don't argue with Nana.",
    "vale": "Observe: the subscribe button. Consider it pressed.",
}
FORMAT_ASK = {"lab_log": "beaker", "tea_ruling": "nana", "deduction": "vale", "rivalry": "identity", "vote": "identity", "backstory": "nana"}

IDEAS = ["Grimm files an objection against Monday", "Nana Rosa rules on the last biscuit", "Vale cross-examines a cat that knocked a glass off a table",
         "Grimm tries to prove gravity is optional (it is not)", "the court's first ever recess: who drank Nana's tea?", "Vale's 15-second case: the missing sock",
         "Grimm vs. a self-checkout machine", "Nana Rosa explains black holes with a teacup"]

def _vsize(): return (360, 640) if SMALL else (1080, 1920)

def spent_this_month():
    """This month's spend on specials: every Cost_Log row of a special reel (episode id 'SP…': clips, pictures) plus the concept call (role 'special')."""
    mk = now_utc().strftime("%Y-%m"); tot = 0.0
    for r in store().rows("Cost_Log"):
        if r.get("basis") == "summary" or not str(r.get("ts", "")).startswith(mk): continue
        if str(r.get("episode_id") or "").startswith("SP") or str(r.get("role") or "") == "special":
            try: tot += float(r.get("inr") or 0)
            except Exception: pass
    return tot

def est_inr(n_clips):
    fx = S("USD_INR", float) or 99.0
    from whatifs.media import still_usd
    return n_clips * S("PRICE_KLING_USD", float) * fx + 4 * still_usd(576, 1024) * fx + 2.0

def allowed(n_clips):
    e = est_inr(n_clips)
    if e > S("SPECIAL_REEL_CAP_INR", float): return False, f"estimated Rs {e:.0f} is above the per-reel cap Rs {S('SPECIAL_REEL_CAP_INR', float):.0f}"
    if spent_this_month() + e > S("SPECIALS_EARMARK_INR", float): return False, "this month's specials money is used"
    return True, f"Rs {e:.0f}"

def _portrait(who, workdir, episode):
    """A locked portrait for the cast member (downloaded from Drive), or a freshly drawn one (counted as the reel's cost)."""
    from whatifs import media as MD, show as SHOW, publish as PUB
    rows = [r for r in store().rows("Character_Sheets") if r.get("character") == who and r.get("status") == "LOCKED" and r.get("file")]
    path = os.path.join(workdir, f"{who}.png")
    if rows and not FAKE:
        try:
            PUB.drive_download(str(rows[0]["file"]).replace("drive:", ""), path); return path
        except Exception as e: log(f"portrait download failed for {who}: {scrub(e)[:80]}", "WARN", episode)
    if who == "SET": desc = "an old grand courtroom at night, tall carved wooden doors, warm lamps, rain on tall windows"
    else:
        c = next((x for x in SHOW.CHARACTERS if x["id"] == who), {})
        desc = f"portrait of {c.get('name', who)}, {c.get('visual', '')}, proud and confident, waist-up"
    W, H = _vsize()
    MD.still(f"{desc}, {LOOK_SUFFIX}", path, episode, seed=f"special|{who}", w=576, h=1024)
    return path

def _face_ok(clip, portrait, who, episode):
    """G1 face consistency (K139): one frame of the animated clip vs the locked portrait, judged by the vision model (about ₹0.2).
    True when it is the same character or the judge cannot answer (never blocks); False only on a clear 'different person'."""
    if not S("FACE_CHECK_ON", bool) or who == "SET": return True
    import base64, tempfile
    from whatifs.models import ask_vision
    f = os.path.join(os.path.dirname(clip), f"{who}_check.jpg")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", "1.5", "-i", clip, "-frames:v", "1", "-vf", "scale=384:-2", f], check=False)
    if not os.path.exists(f) or not os.path.exists(portrait): return True
    imgs = [("image/jpeg", base64.b64encode(open(f, "rb").read()).decode()), ("image/png", base64.b64encode(open(portrait, "rb").read()).decode())]
    r = ask_vision("You compare two images of an animated character. Return JSON {\"same_person\": true|false, \"note\": \"\"}. false ONLY if the face is clearly a different person or badly distorted.",
                   "Image 0 is a frame from a video; image 1 is the reference portrait.", imgs, episode)
    return not (isinstance(r, dict) and r.get("same_person") is False)

def _portrait_motion(portrait, out, sec, W, H):
    """₹0 fallback: a slow push-in on the locked portrait (used when the animated face drifted)."""
    frames = int(sec * 30) + 15
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", portrait, "-vf",
                    f"scale={W * 2}:{H * 2}:force_original_aspect_ratio=increase,crop={W * 2}:{H * 2},zoompan=z='min(zoom+0.0012,1.12)':d={frames}:s={W}x{H}:fps=30",
                    "-t", f"{sec + 0.5:.2f}", "-pix_fmt", "yuv420p", out], check=True, timeout=300)
    return out

def _wrap(d, text, f, maxw):
    words, lines, cur = str(text).split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if d.textlength(trial, font=f) <= maxw or not cur: cur = trial
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

def _card_png(text, sub, path, W, H, end=False):
    """Title + line, word-wrapped inside 84% of the width and kept in the upper-middle of the frame (clear of the Shorts/Reels buttons and caption
    area: the block ends above 64% of the height, i.e. at least 36% up from the bottom)."""
    from PIL import Image, ImageDraw
    from whatifs.media import font
    im = Image.new("RGBA", (W, H), (14, 16, 30, 255) if end else (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    maxw = int(W * 0.84); blocks = []
    for txt, size, bold, col in ((text, 0.058 if end else 0.052, True, (255, 214, 0, 255)), (sub, 0.032, False, (236, 238, 246, 255))):
        if not txt: continue
        sz = int(H * size)
        while True:
            f = font(sz, bold=bold); lines = _wrap(d, txt, f, maxw)
            if all(d.textlength(l, font=f) <= maxw for l in lines) and len(lines) <= 3 or sz < 18: break
            sz = int(sz * 0.9)
        blocks.append((lines, f, col))
    total = sum(len(ls) * int(f.size * 1.3) for ls, f, _ in blocks) + (int(H * 0.012) if len(blocks) > 1 else 0)
    y = int(H * (0.34 if end else 0.62)) - total
    y = max(int(H * 0.30), y)
    for ls, f, col in blocks:
        for l in ls:
            w = d.textlength(l, font=f); x = int((W - w) / 2)
            d.text((x + 2, y + 2), l, font=f, fill=(0, 0, 0, 210)); d.text((x, y), l, font=f, fill=col); y += int(f.size * 1.3)
        y += int(H * 0.012)
    im.save(path); return path

def _sound(total, beats, path, sr=48000):
    """Original sound by code: a rising drone, a hit on every beat change, a low boom on the title, a soft tail. Peak-normalised (-1 dBFS)."""
    n = int(total * sr); t = np.arange(n) / sr
    drone = 0.18 * np.sin(2 * np.pi * (55 + 25 * t / total) * t) * np.minimum(1, t / 1.5)
    noise = np.random.default_rng(7).standard_normal(n) * 0.02 * (t / total)
    out = drone + noise; at = 0.0
    for i, b in enumerate(beats):
        k = int(at * sr); L = int(0.35 * sr)
        if k + L < n:
            env = np.exp(-np.linspace(0, 6, L)); f = 80 if i < len(beats) - 1 else 45
            out[k:k + L] += (0.6 if i < len(beats) - 1 else 0.9) * env * np.sin(2 * np.pi * f * np.arange(L) / sr)
        at += b
    out = out / (np.max(np.abs(out)) + 1e-9) * 0.89
    st = np.stack([out, out], 1).astype(np.float32)
    import soundfile as sf
    sf.write(path, st, sr); return path

def _assemble(clips, beats, cards, end_card, sound, out_path, W, H):
    """Clips (cropped to 9:16, trimmed), crossfaded, card overlays faded in, the end card, the sound. One ffmpeg run."""
    inputs, filt = [], []
    for i, c in enumerate(clips):
        inputs += ["-i", c]
        filt.append(f"[{i}:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps=30,trim=0:{beats[i]:.2f},setpts=PTS-STARTPTS,format=yuv420p[v{i}]")
    k = len(clips)
    for j, cp in enumerate(cards): inputs += ["-loop", "1", "-t", f"{beats[j]:.2f}", "-i", cp]
    inputs += ["-loop", "1", "-t", "2.5", "-i", end_card, "-i", sound]
    for j in range(len(cards)):
        filt.append(f"[{k + j}:v]scale={W}:{H},setsar=1,fps=30,format=rgba,fade=t=in:st=0.3:d=0.4:alpha=1[c{j}];[v{j}][c{j}]overlay=0:0:shortest=1,format=yuv420p,setsar=1[o{j}]")
    filt.append(f"[{k + len(cards)}:v]scale={W}:{H},setsar=1,fps=30,format=yuv420p[endv]")
    labels = [f"[o{j}]" for j in range(len(cards))] + ["[endv]"]
    filt.append("".join(labels) + f"concat=n={len(labels)}:v=1:a=0[vout]")
    total = sum(beats) + 2.5
    cmd = ["ffmpeg", "-y", "-loglevel", "error"] + inputs + ["-filter_complex", ";".join(filt), "-map", "[vout]", "-map", f"{k + len(cards) + 1}:a",
                                                         "-t", f"{total:.2f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
                                                         "-c:a", "aac", "-b:a", "160k", "-shortest", out_path]
    subprocess.run(cmd, check=True, timeout=600)
    return out_path

def _format_scores():
    """Median engaged views at 7 days per format (from the Specials tab)."""
    import statistics
    per = {}
    for r in store().rows("Specials"):
        try: v = float(r.get("views_7d"))
        except (TypeError, ValueError): continue
        per.setdefault(r.get("format"), []).append(v)
    return {f: statistics.median(v) for f, v in per.items() if v}

def pick_format(now=None, seed=None):
    """Weighted choice: base weights x learned performance (exploration floor 0.5x), lore drops at most one per SPECIALS_LORE_MIN_DAYS."""
    import random
    now = now or now_utc(); rows = store().rows("Specials")
    last_lore = max([str(r.get("ts", "")) for r in rows if r.get("format") == "backstory"] or [""])
    lore_ok = not last_lore or (now - parse_iso(last_lore)).days >= S("SPECIALS_LORE_MIN_DAYS", int)
    sc = _format_scores(); med = sorted(sc.values())[len(sc) // 2] if sc else 0
    weights = {}
    for f, d in FORMATS.items():
        if f == "backstory" and not lore_ok: continue
        perf = (sc[f] / med) if (f in sc and med) else 1.0
        weights[f] = d["w"] * max(0.5, min(2.0, perf))
    last = rows[-1].get("format") if rows else ""
    if last in weights and len(weights) > 1: weights[last] *= 0.3                    # rarely the same format twice in a row
    rng = random.Random(seed or now.strftime("%Y%m%d"))
    return rng.choices(list(weights), weights=list(weights.values()), k=1)[0]

def _canon_fact(fmt):
    used = {r.get("title") for r in store().rows("Specials") if r.get("format") == "backstory"}
    who = FORMATS[fmt]["who"]
    facts = [f for c, f in CANON if c == who] or [f for _, f in CANON]
    n = len([r for r in store().rows("Specials") if r.get("format") == "backstory"])
    return facts[n % len(facts)]

def _occasion_concept(key):
    from whatifs.occasions import OCCASIONS, FAMILY_ASK
    name, _r, brief = OCCASIONS[key]
    return {"format": "occasion", "occasion": key, "name": name, "brief": brief, "ask": FAMILY_ASK}

def concept(kind, fmt=None, occasion=None, topical=""):
    if kind == "cast_intro":
        beats = [dict(b) for b in CAST_INTRO]
        fest = str(S("CAST_INTRO_FESTIVE") or "").strip()
        if fest:                                                   # e.g. "Diwali": the courtroom glows with lamps and the court greets the viewers
            beats[-1]["motion"] += ", the courtroom glowing with rows of small oil lamps and warm festive lights"
            beats[-1]["line"] = f"Happy {fest} from the court. Tuesday: you're the jury."
        return {"title": "Meet the court: Reality on Trial", "beats": beats, "format": "cast_intro", "ask": ASKS["identity"]}
    from whatifs.models import ask
    occ = _occasion_concept(occasion) if occasion else None
    fmt = "occasion" if occ else (fmt or pick_format())
    if occ: brief = f"{occ['name']} special: {occ['brief']} Last beat: a warm, slightly touching family moment and the line '{occ['ask']}'"
    else:
        n = 1 + len([r for r in store().rows("Specials") if r.get("format") == fmt])
        brief = FORMATS[fmt]["brief"].replace("{n}", str(n))
        if topical: brief += f" Tie it, lightly and accurately, to this week's topic: {topical}."
    extra = {"canon_fact": _canon_fact(fmt)} if fmt == "backstory" else {}
    used = {r.get("title") for r in store().rows("Specials")}
    sysm = ("Write a 12-15 second vertical reel for a witty science-courtroom show with three original characters: Inspector Vale (calm detective, grey "
            "overcoat, silver-rimmed glasses), Dr. Grimm (theatrical skeptic, black high-collar coat, red pocket square) and Nana Rosa (unimpressed judge, "
            "silver bun, floral teacup). Make viewers fall for the characters: specific details, one laugh or one warm moment, characters true to "
            "their bible. Family-friendly. No real people, no other shows' characters, no abuse, injury, self-harm or tragedy detail. "
            "JSON only: {title, beats:[{who: VALE|GRIMM|ROSA|SET, sec: 3-3.5, motion: one cinematic camera+action sentence, card: 1-4 WORDS, "
            "line: max 8 words}]} with exactly 4 beats.")
    out = ask("special", sysm, json.dumps({"format": fmt, "brief": brief, **extra, "avoid_titles": sorted(t for t in used if t)}, ensure_ascii=False),
              want_json=True, max_tokens=1500, fake_key="special")
    beats = [b for b in (out or {}).get("beats", []) if isinstance(b, dict) and b.get("who") in ("VALE", "GRIMM", "ROSA", "SET")][:4] if isinstance(out, dict) else []
    if len(beats) < 3: return {"title": "Meet the court: Reality on Trial", "beats": [dict(b) for b in CAST_INTRO], "format": "cast_intro", "ask": ASKS["identity"]}
    for b in beats: b["sec"] = float(min(3.5, max(2.5, float(b.get("sec") or 3))))
    ask_line = occ["ask"] if occ else ASKS[FORMAT_ASK.get(fmt, "identity")]
    return {"title": str(out.get("title") or "Reality on Trial")[:80], "beats": beats, "format": fmt if not occ else f"occasion:{occasion}", "ask": ask_line}

def record_views(now=None):
    """Learning job: engaged views of each special at 7 days (public views as the fallback), for the format weights. Never raises."""
    from whatifs import publish as PUB
    now = now or now_utc(); st = store(); n = 0
    for r in st.rows("Specials"):
        t = parse_iso(r.get("ts"))
        if not r.get("yt_id") or r.get("views_7d") not in (None, "") or not t or (now - t).days < 7: continue
        try:
            v = PUB.yt_engaged_views(r["yt_id"], t.strftime("%Y-%m-%d"))
            if v is None: v = PUB.yt_views(r["yt_id"])
            if v is not None: st.update("Specials", "id", r["id"], {"views_7d": int(v)}); n += 1
        except Exception as e: log(f"special views not read: {scrub(e)[:80]}", "WARN")
    return n

def run(kind="special", force=False, publish=True):
    """Make (and post) one special reel. Returns a dict; never raises (fail-forward: nothing posted on any error)."""
    episode = f"SP{now_utc():%Y%m%d%H%M}"
    try:
        if not S("SPECIALS_ON", bool) and not force: return {"ok": False, "why": "SPECIALS_ON is FALSE"}
        from whatifs import shortslab as SL
        if kind != "cast_intro" and not SL.allowed_today(): return {"ok": False, "why": "the 14-Shorts-a-week ceiling is reached"}
        occasion, topical = None, ""
        if kind == "special":
            from whatifs import occasions as OC
            occasion = OC.slot_for(now_utc().date()) or None
            if not occasion and S("SPECIALS_TOPICAL_ON", bool): topical = OC.topical_hook()
        c = concept(kind, occasion=occasion, topical=topical); beats = c["beats"]
        ok, why = allowed(len(beats))
        if not ok: log(f"special reel not made: {why}", "WARN", episode); return {"ok": False, "why": why}
        from whatifs import media as MD
        W, H = _vsize(); wd = os.path.join(WORK, episode); os.makedirs(wd, exist_ok=True)
        clips, cards = [], []
        for i, b in enumerate(beats):
            img = _portrait(b["who"], wd, episode)
            clip = os.path.join(wd, f"clip{i}.mp4")
            MD.animate(None, img, f"{b['motion']}, {LOOK_SUFFIX}", clip, episode, hero=True)
            try:
                if not _face_ok(clip, img, b["who"], episode):                # the face drifted: the locked portrait carries the beat (never a second paid clip)
                    log(f"special: {b['who']}'s face drifted in the animation; using the locked portrait instead", "WARN", episode)
                    clip = _portrait_motion(img, os.path.join(wd, f"clip{i}_portrait.mp4"), b["sec"], W, H)
            except Exception as e: log(f"face check skipped: {scrub(e)[:100]}", "WARN", episode)
            clips.append(clip); cards.append(_card_png(b.get("card", ""), b.get("line", ""), os.path.join(wd, f"card{i}.png"), W, H))
        end = _card_png(c.get("ask") or ASKS["identity"], "Reality Engine on YouTube + Instagram", os.path.join(wd, "end.png"), W, H, end=True)
        snd = _sound(sum(b["sec"] for b in beats) + 2.5, [b["sec"] for b in beats], os.path.join(wd, "sound.wav"))
        out = _assemble(clips, [b["sec"] for b in beats], cards, end, snd, os.path.join(wd, f"{episode}.mp4"), W, H)
        rec = {"ts": iso(), "id": episode, "kind": kind, "title": c["title"], "format": c.get("format", ""), "ask": c.get("ask", ""), "yt_id": "", "ig": "", "fb": "", "status": "MADE", "views_7d": ""}
        if publish: rec.update(_publish(out, c["title"], episode))
        store().append("Specials", [rec]); log(f"special reel {episode} ({kind}) {rec['status']}", episode=episode)
        return {"ok": True, **rec, "path": out}
    except Exception as e:
        log(f"special reel failed (nothing posted): {scrub(e)[:200]}", "WARN", episode); return {"ok": False, "why": str(e)[:200]}

def _publish(path, title, episode):
    from whatifs import publish as PUB, launch as LA
    res = {"status": "MADE"}
    if not LA.uploads_open(): res["status"] = "HELD (uploads not confirmed open)"; return res
    desc = (f"{title}\nNew trials every Tuesday and Saturday: Reality on Trial on the Reality Engine channel. Take your seat on the jury: subscribe.\n"
            "AI-assisted visuals; original characters and story.")
    try: res["yt_id"] = PUB.yt_upload(path, title[:90], desc, ["reality on trial", "what if"], short=True, ai_label=True)
    except Exception as e: log(f"special: YouTube upload failed: {scrub(e)[:120]}", "WARN", episode)
    links, opened = {}, []
    def link(p):
        if p not in links:
            fid, url = PUB.drive_upload(p, os.path.basename(p), public=True); opened.append(fid); links[p] = url
        return links[p]
    if not PUB.meta_ready():                                      # v10.1: Meta not connected yet: YouTube only, no Drive link opened
        log("special: Instagram/Facebook not connected - posted to YouTube only", "INFO", episode)
        res["status"] = "POSTED" if res.get("yt_id") else "MADE (not posted)"; return res
    try:
        try: res["ig"] = str(PUB.ig_reel(None, desc.replace("Reality Engine channel", "Reality Engine channel (link in bio)"), None, video_path=path, url_fn=lambda: link(path)) or "")
        except Exception as e: log(f"special: Instagram failed: {scrub(e)[:120]}", "WARN", episode)
        try: res["fb"] = str(PUB.fb_reel(None, desc, video_path=path, url_fn=lambda: link(path)) or "")
        except Exception as e: log(f"special: Facebook failed: {scrub(e)[:120]}", "WARN", episode)
    finally:
        for fid in opened:
            try: PUB.drive_private(fid)
            except Exception: pass
    res["status"] = "POSTED" if res.get("yt_id") else "MADE (not posted)"
    return res

def due(now=None):
    """True on this month's special slots (occasions first, then SPECIALS_DAYS) when no special was made that day."""
    from whatifs import occasions as OC
    now = now or now_utc()
    if OC.slot_for(now.date()) is None: return False
    return not any(str(r.get("ts", "")).startswith(now.strftime("%Y-%m-%d")) and r.get("kind") == "special" for r in store().rows("Specials"))
