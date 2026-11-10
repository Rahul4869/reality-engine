"""One-time, hand-started clip-model bake-off: the same scenes animated by the current hero model and each candidate, capped by BAKEOFF_CAP_INR. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import os
from whatifs.core import S, log, store, iso, now_utc, FAKE, WORK, scrub, set_setting

SCENES = ["a lone astronaut standing on a red desert as a giant planet rises behind, wind moving the dust, cinematic",
          "an old courtroom at night, rain on tall windows, a teacup steaming on the judge's bench, slow push-in, cinematic"]

def _models():
    ms = [x.strip() for x in str(S("BAKEOFF_CLIP_MODELS") or "").split(",") if x.strip()]
    ps = [float(x) for x in str(S("BAKEOFF_CLIP_PRICES") or "").split(",") if x.strip()]
    out = [(S("FAL_HERO_MODEL"), S("PRICE_KLING_USD", float))]
    for i, m in enumerate(ms):
        if m != out[0][0]: out.append((m, ps[i] if i < len(ps) else S("PRICE_KLING_USD", float)))
    return out[:3]

def run(force=False):
    if str(S("BAKEOFF_DONE") or "").strip() and not force: return {"ok": False, "why": "already done (BAKEOFF_DONE)"}
    from whatifs import media as MD, publish as PUB, notify as NT
    fx = S("USD_INR", float) or 99.0; models = _models()
    est = sum(p for _, p in models) * len(SCENES) * fx + 2
    if est > S("BAKEOFF_CAP_INR", float): return {"ok": False, "why": f"estimate Rs {est:.0f} is above BAKEOFF_CAP_INR"}
    ep = f"BK{now_utc():%Y%m%d%H%M}"; wd = os.path.join(WORK, ep); os.makedirs(wd, exist_ok=True); links = {}
    for si, scene in enumerate(SCENES):
        img = os.path.join(wd, f"s{si}.png"); MD.still(scene, img, ep, seed=f"bake|{si}", w=576, h=1024)
        for mi, (m, p) in enumerate(models):
            out = os.path.join(wd, f"s{si}_m{mi}.mp4")
            try: MD.animate(None, img, scene, out, ep, hero=True, model=m, price_usd=p)
            except Exception as e: log(f"bake-off: {m} skipped ({scrub(e)[:80]})", "WARN", ep); continue
            if not FAKE:
                try: _fid, url = PUB.drive_upload(out, f"bakeoff_scene{si + 1}_model{mi + 1}.mp4", public=False); links.setdefault(mi, []).append(url)
                except Exception as e: log(f"bake-off upload failed: {scrub(e)[:80]}", "WARN", ep)
            else: links.setdefault(mi, []).append(out)
    names = "; ".join(f"{i + 1}) {m.split('/')[-2] if '/' in m else m} (${p}/clip)" + (" [current]" if i == 0 else "") for i, (m, p) in enumerate(models))
    body = "Model bake-off ready: the same 2 scenes by each video model. " + names + ". Clips: " + " | ".join(f"model {i + 1}: " + ", ".join(f"<a href='{u}'>scene {k + 1}</a>" for k, u in enumerate(v)) for i, v in links.items())
    buttons = [("Keep current", "BAKE 0")] + [(f"Use {i + 1}", f"BAKE {i}") for i in range(1, len(models))]
    aid = NT.send("bakeoff", body, buttons, tier="now", default="keep the current model", expires_h=48)
    set_setting("BAKEOFF_DONE", iso()); store().append("Bakeoff", [{"ts": iso(), "models": names[:400], "card": aid}])
    return {"ok": True, "card": aid, "models": len(models)}

def _answer(row, choice):
    try: i = int(str(choice).split()[-1])
    except ValueError: return "recorded"
    models = _models()
    if i <= 0 or i >= len(models): return "kept the current model"
    m, p = models[i]; set_setting("FAL_HERO_MODEL", m); set_setting("PRICE_KLING_USD", str(p))
    return f"hero model set to {m}"

def register():
    from whatifs import notify as NT
    NT.register("bakeoff", on_answer=_answer)

def judge_pair(cur_id, cur_usd, new_id, new_usd):
    """v10.1 (K150): automatic capped test for the Model Steward: the same 2 scenes by the current and the candidate model; 3 frames of each
    clip scored 0-10 by the vision model (motion realism, artifacts, prompt match). {'ok', 'cur_score', 'new_score'} or {'ok': False}."""
    import base64, subprocess
    from whatifs import media as MD
    from whatifs.models import ask_vision
    fx = S("USD_INR", float) or 99.0
    if (cur_usd + new_usd) * len(SCENES) * fx + 2 > S("BAKEOFF_CAP_INR", float): return {"ok": False, "why": "above BAKEOFF_CAP_INR"}
    ep = f"BKA{now_utc():%Y%m%d%H%M}"; wd = os.path.join(WORK, ep); os.makedirs(wd, exist_ok=True); scores = {}
    for tag, (m, p) in (("cur", (cur_id, cur_usd)), ("new", (new_id, new_usd))):
        vals = []
        for si, scene in enumerate(SCENES):
            img = os.path.join(wd, f"s{si}.png")
            if not os.path.exists(img): MD.still(scene, img, ep, seed=f"bake|{si}", w=576, h=1024)
            out = os.path.join(wd, f"{tag}{si}.mp4")
            try: MD.animate(None, img, scene, out, ep, hero=True, model=m, price_usd=p)
            except Exception as e: log(f"auto test: {m} failed ({str(e)[:80]})", "WARN", ep); vals.append(0.0); continue
            frames = []
            for t in (0.8, 2.5, 4.2):
                f = os.path.join(wd, f"{tag}{si}_{t}.jpg")
                subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(t), "-i", out, "-frames:v", "1", "-vf", "scale=384:-2", f], check=False)
                if os.path.exists(f): frames.append(("image/jpeg", base64.b64encode(open(f, "rb").read()).decode()))
            r = ask_vision("Score these 3 frames from one AI video clip, 0-10, for cinematic quality: realistic motion, no melted faces or glitches, "
                           "sharpness, and match to the prompt. JSON only: {\"score\": number}", f"PROMPT: {scene}", frames, ep) if frames else None
            try: vals.append(float((r or {}).get("score")))
            except (TypeError, ValueError): vals.append(5.0)
        scores[tag] = sum(vals) / max(1, len(vals))
    store().append("Bakeoff", [{"ts": iso(), "models": f"auto: {cur_id} {scores.get('cur', 0):.1f} vs {new_id} {scores.get('new', 0):.1f}", "card": ""}])
    return {"ok": True, "cur_score": scores.get("cur", 0.0), "new_score": scores.get("new", 0.0)}

