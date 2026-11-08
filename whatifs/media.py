"""whatifs/media.py v8.3 - fal.ai images/clips, free NASA/Pexels footage, depth maps, motion graphics, fake assets for rehearsal."""
from __future__ import annotations
import os, time, json, hashlib, random, subprocess
import numpy as np, requests
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from whatifs.core import env, log, cost, S, FAKE, note_degraded, DEFAULTS
from whatifs.governor import fal_allowed

FAL = "https://queue.fal.run/"
def FH(): return {"Authorization": "Key " + env("FAL_KEY"), "Content-Type": "application/json"}

def fal_run(model_id, args, timeout=900):
    r = requests.post(FAL + model_id, headers=FH(), json=args, timeout=60)
    if r.status_code >= 400: raise RuntimeError(f"fal submit {r.status_code}: {r.text[:300]}")
    j = r.json(); st_url, res_url = j.get("status_url"), j.get("response_url")
    t0 = time.time()
    while time.time() - t0 < timeout:
        try: s = requests.get(st_url, headers=FH(), timeout=30).json()
        except (requests.RequestException, ValueError) as e:          # v8.9.3: one bad status answer no longer abandons a job that is already paid for
            log(f"fal status check failed ({str(e)[:120]}) - asking again", "WARN"); time.sleep(5); continue
        if s.get("status") == "COMPLETED": break
        if s.get("status") in ("FAILED", "ERROR"): raise RuntimeError(f"fal failed: {s}")
        time.sleep(3)
    else: raise RuntimeError("fal timeout")
    res = None
    for a in range(3):
        try:
            res = requests.get(res_url, headers=FH(), timeout=60)
            if res.status_code < 500: break
        except requests.RequestException as e: log(f"fal result fetch failed ({str(e)[:120]})", "WARN")
        time.sleep(5 * (a + 1))
    if res is None or res.status_code >= 400:                         # v8.9.3: a failed generation answers here with an error, not with images
        raise RuntimeError(f"fal result {getattr(res, 'status_code', 'unreachable')}: {(res.text if res is not None else '')[:300]}")
    return res.json()

def _dl(url, path):
    with requests.get(url, stream=True, timeout=300) as r:
        r.raise_for_status()
        with open(path, "wb") as f:
            for c in r.iter_content(1 << 20): f.write(c)
    return path

# ---------------- fake assets (rehearsal) ----------------
def fake_image(path, w, h, seed, label=""):
    rng = random.Random(seed); img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    c1 = (rng.randint(0, 60), rng.randint(20, 90), rng.randint(60, 140)); c2 = (rng.randint(150, 255), rng.randint(80, 180), rng.randint(20, 90))
    for y in range(h):
        k = y / h; d.line([(0, y), (w, y)], fill=tuple(int(c1[i] * (1 - k) + c2[i] * k) for i in range(3)))
    for _ in range(18):
        x, y, r = rng.randint(0, w), rng.randint(0, h), rng.randint(h // 30, h // 6)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(rng.randint(0, 255), rng.randint(0, 255), rng.randint(0, 255)))
    img = img.filter(ImageFilter.GaussianBlur(2))
    if label: ImageDraw.Draw(img).text((20, 20), label[:60], fill=(255, 255, 255))
    img.save(path, quality=92); return path

def fake_clip(path, w, h, seed, sec=5):
    img = fake_image(path + ".jpg", w, h, seed)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", img, "-t", str(sec), "-vf",
                    f"scale={w*1.1:.0f}:-2,crop={w}:{h}:'(iw-ow)/2+sin(t)*20':'(ih-oh)/2',format=yuv420p", "-r", "30", path], check=True)
    os.remove(img); return path

# ---------------- images ----------------
def still_usd(w, h):
    """v10.1: FLUX schnell on fal bills per megapixel rounded UP (verified 8 Nov 2026)."""
    import math
    return S("PRICE_STILL_PER_MP", float) * max(1, math.ceil((w * h) / 1e6))

def video_args(model, image_url, prompt, hero=False):
    """v10.1: each fal video model names its inputs differently (verified 8 Nov 2026): Kling 2.6 Pro wants start_image_url and has audio ON by
    default; Wan 2.6 wants a resolution; Kling 2.5 Turbo Pro takes cfg_scale. Unknown models get the plain prompt + image_url."""
    m = str(model or "")
    neg = "blur, distort, and low quality, text, watermark"
    if "kling-video/v2.6" in m: return {"prompt": prompt, "start_image_url": image_url, "duration": "5", "negative_prompt": neg, "generate_audio": False}
    if "kling-video/v2.5-turbo" in m: return {"prompt": prompt, "image_url": image_url, "duration": "5", "negative_prompt": neg, "cfg_scale": 0.5}
    if m.startswith("wan/v2.6"): return {"prompt": prompt, "image_url": image_url, "resolution": "720p", "duration": "5"}
    if "hailuo" in m: return {"prompt": prompt, "image_url": image_url, "duration": "6"}
    args = {"prompt": prompt, "image_url": image_url}
    if hero: args.update({"duration": "5", "negative_prompt": neg})
    return args

RETIRED_MODELS = ("fal-ai/veo3.1", "fal-ai/kling-video/v2.1/")          # v10.1: retired or being retired on fal (Nov 2026)

def still(prompt, path, episode, seed=None, w=None, h=None, premium=False, model=None):
    w = w or S("STILL_W", int); h = h or S("STILL_H", int)
    from whatifs import v91 as V91
    if V91.on("LIGHTING_DIRECTIVE_ON"):                      # v9.1: lighting + composition directive (the style lock is added after it, never cut)
        with V91.guard("LIGHTING_DIRECTIVE_ON"):
            from whatifs.atmosphere import with_directive
            lock_ = str(S("STYLE_LOCK") or "").strip()
            prompt = with_directive(prompt, S("IMAGE_PROMPT_MAX_CHARS", int) - (len(lock_) + 2 if lock_ and not premium else 0), vertical=h > w)
    if FAKE: return fake_image(path, w, h, seed or prompt, prompt), None
    if not fal_allowed(): raise RuntimeError("fal credit exhausted")
    model = model or (S("FAL_PREMIUM_MODEL") if premium else S("FAL_STILL_MODEL"))      # v10: an explicit model only for the bake-off
    lock = str(S("STYLE_LOCK") or "").strip()
    if not premium and lock and lock not in prompt: prompt = prompt.rstrip(". ") + ". " + lock      # v8.9: repair stills keep the same look
    args = {"prompt": prompt, "image_size": {"width": w, "height": h}, "num_images": 1, "enable_safety_checker": True}
    if not premium: args["num_inference_steps"] = 4
    else: args["safety_tolerance"] = "2"
    if seed is not None: args["seed"] = int(hashlib.md5(str(seed).encode()).hexdigest()[:7], 16)
    out = fal_run(model, args)
    mp = w * h / 1e6
    cost("image_premium" if premium else "image", "fal", 1, (S("PRICE_THUMB_USD", float) if premium else still_usd(w, h)), episode)   # v10.1: real megapixel rounding(it is billed), before the download can fail
    url = out["images"][0]["url"]; _dl(url, path)
    return path, url

def _data_uri(image_path):
    """v8.9.1: a picture we already own, as a base64 data URI (fal accepts data URIs for file inputs), so a restored picture whose URL was lost
    can still be animated without buying it again."""
    import base64
    with open(image_path, "rb") as f: b = f.read()
    mime = "image/png" if str(image_path).lower().endswith(".png") else "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(b).decode("ascii")

def animate(image_url, image_path, prompt, path, episode, hero=False, model=None, price_usd=None):
    if FAKE: return fake_clip(path, S("STILL_W", int), S("STILL_H", int), prompt, 5)
    if not image_url:              # v8.9.1 (fix): a missing URL in production used to return the offline TEST clip; now the real picture is sent, or it fails loudly
        if not image_path or not os.path.exists(image_path): raise RuntimeError("no picture to animate (no URL and no file)")
        image_url = _data_uri(image_path)
    if not fal_allowed(): raise RuntimeError("fal credit exhausted")
    explicit = model is not None
    role = "hero" if hero else "living"
    model = model or (S("FAL_HERO_MODEL") if hero else S("FAL_LIVING_MODEL"))          # v10: an explicit model only for the bake-off
    if hero and any(str(model).startswith(r) for r in RETIRED_MODELS):
        log(f"video model {model} is retired on fal; using {DEFAULTS['FAL_HERO_MODEL'][0]}", "WARN", episode); model = DEFAULTS["FAL_HERO_MODEL"][0]
    from whatifs import steward as STW
    if not explicit and S("MODEL_STEWARD_ON", bool): model = STW.ensure(role, model)
    if model == STW.CODE_MOTION: return _code_motion(image_path, path)
    try:
        out = _fal_video(model, image_url, image_path, prompt, path, episode, hero, price_usd)
        STW.report_success(model); return out
    except Exception as e:
        if explicit or not S("MODEL_STEWARD_ON", bool): raise
        nxt = STW.report_failure(role, model, e)
        if not nxt or nxt == model: raise
        log(f"retrying with {nxt} after: {str(e)[:120]}", "WARN", episode)
        if nxt == STW.CODE_MOTION: return _code_motion(image_path, path)
        return _fal_video(nxt, image_url, image_path, prompt, path, episode, hero, None)

def _code_motion(image_path, path, sec=5.0):
    """v10.1 (K150): the ₹0 last rung for living stills: a slow push-in on the picture we already own."""
    if not image_path or not os.path.exists(image_path): raise RuntimeError("code motion needs the picture file")
    from whatifs.specials import _portrait_motion
    W, H = S("STILL_W", int), S("STILL_H", int)
    return _portrait_motion(image_path, path, sec, W - W % 2, H - H % 2)

def _fal_video(model, image_url, image_path, prompt, path, episode, hero, price_usd):
    if not image_url:
        image_url = _data_uri(image_path)
    args = video_args(model, image_url, prompt, hero)
    out = fal_run(model, args, timeout=1500)
    cost("hero_clip" if hero else "living_clip", "fal", 1, price_usd if price_usd is not None else (S("PRICE_KLING_USD", float) if hero else S("PRICE_LIVING_USD", float)), episode)      # v8.3: logged before the download
    url = (out.get("video") or {}).get("url")
    if not url: raise RuntimeError(f"no video in fal reply: {str(out)[:200]}")
    _dl(url, path)
    return path

# ---------------- free real footage ----------------
def stock(query, path, episode):
    if FAKE: return fake_clip(path, 1280, 720, query, 6)
    for fn in (_nasa, _pexels):
        try:
            if fn(query, path): return path
        except Exception as e: log(f"stock {fn.__name__} failed: {e}", "WARN", episode)
    return None

def _nasa(q, path):
    r = requests.get("https://images-api.nasa.gov/search", params={"q": q, "media_type": "video"}, timeout=30).json()
    for it in r.get("collection", {}).get("items", [])[:8]:
        d = (it.get("data") or [{}])[0]
        if "copyright" in json.dumps(d).lower(): continue
        files = requests.get(it["href"], timeout=30).json()
        mp4 = [f for f in files if f.endswith(".mp4")]
        pick = next((f for f in mp4 if "~medium" in f), None) or next((f for f in mp4 if "~mobile" in f), None) or (mp4[0] if mp4 else None)
        if pick:
            _dl(pick.replace("http://", "https://").replace(" ", "%20"), path)
            if os.path.getsize(path) > 200_000: return True
    return False

def _pexels(q, path):
    k = env("PEXELS_KEY")
    if not k: return False
    r = requests.get("https://api.pexels.com/videos/search", params={"query": q, "per_page": 5, "orientation": "landscape"}, headers={"Authorization": k}, timeout=30).json()
    for v in r.get("videos", []):
        files = sorted([f for f in v.get("video_files", []) if (f.get("width") or 0) >= 1280], key=lambda f: f.get("width") or 0)
        if files:
            _dl(files[0]["link"], path); return True
    return False

# ---------------- depth ----------------
_depth = None
def depth_map(img_path):
    """Depth-Anything-V2-Small (Apache-2.0). Falls back to a centre-weighted map."""
    global _depth
    im = Image.open(img_path).convert("RGB")
    if not FAKE and S("PARALLAX_ON", bool):
        try:
            if _depth is None:
                from transformers import pipeline
                _depth = pipeline("depth-estimation", model="depth-anything/Depth-Anything-V2-Small-hf", device=-1)
            d = np.asarray(_depth(im)["depth"].resize(im.size), dtype=np.float32)
            d = (d - d.min()) / (d.max() - d.min() + 1e-6); return d
        except Exception as e:
            note_degraded("flat depth map instead of the depth model"); log(f"depth model unavailable, using simple depth: {e}", "WARN"); _depth = False if _depth is None else _depth
    w, h = im.size; yy, xx = np.mgrid[0:h, 0:w]
    return (1 - np.sqrt(((xx - w / 2) / w) ** 2 + ((yy - h * 0.55) / h) ** 2) * 1.4).clip(0, 1).astype(np.float32)

# ---------------- motion graphics ----------------
def font(size, bold=True):
    for f in (["fonts/Anton-Regular.ttf"] if bold else []) + ["fonts/Inter-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]:
        if os.path.exists(f):
            ft = ImageFont.truetype(f, size)
            if "Inter" in f:   # the downloaded Inter file is the variable font: select its Bold instance
                try: ft.set_variation_by_name("Bold")
                except Exception:
                    try: ft.set_variation_by_axes([min(size, 32), 700])
                    except Exception: pass
            return ft
    return ImageFont.load_default()

def _fmt(v, unit):
    a = abs(v)
    s = f"{v/1e9:.2f} billion" if a >= 1e9 else f"{v/1e6:.1f} million" if a >= 1e6 else f"{v:,.1f}" if 0 < a < 10 else f"{v:,.0f}"
    return (s + (" " + unit if unit else "")).strip()

def clean_graphic(g):
    """Validate a Director graphic. Returns a safe dict (kind counter | timeline | compare) or None when it cannot be drawn (the shot then becomes a normal still)."""
    if not isinstance(g, dict): return None
    kind = str(g.get("kind") or "counter").lower()
    try:
        if kind == "timeline":
            ev = [{"t": str(x.get("t", ""))[:14], "text": str(x.get("text", ""))[:34]} for x in (g.get("events") or []) if isinstance(x, dict) and x.get("text")][:5]
            return {"kind": "timeline", "label": str(g.get("label", ""))[:48], "events": ev} if len(ev) >= 2 else None
        if kind == "compare":
            a, b = g.get("a") or {}, g.get("b") or {}
            av, bv = float(a.get("value")), float(b.get("value"))
            if av <= 0 or bv <= 0: return None
            return {"kind": "compare", "label": str(g.get("label", ""))[:48], "unit": str(g.get("unit", ""))[:16],
                    "a": {"name": str(a.get("name", "A"))[:22], "value": av}, "b": {"name": str(b.get("name", "B"))[:22], "value": bv}}
        float(g.get("from", 0)); float(g.get("to", 100))
        return dict(g, kind="counter")
    except Exception: return None

def _timeline_frame(g, t, W, H, img, d, ov):
    e = 1 - (1 - min(1, t * 1.15)) ** 3; ev = g["events"]; n = len(ev)
    lab = font(int(H * 0.05)); big = font(int(H * 0.075)); small = font(int(H * 0.04), bold=False)
    d.text((W * 0.08, H * 0.14), str(g.get("label", "")).upper(), font=lab, fill=(120, 220, 255, 255))
    y = H * 0.55; x0, x1 = W * 0.1, W * 0.9
    d.rectangle([x0, y, x1, y + H * 0.008], fill=(255, 255, 255, 70)); d.rectangle([x0, y, x0 + (x1 - x0) * e, y + H * 0.008], fill=(120, 220, 255, 255))
    for k, x in enumerate(ev):
        px = x0 + (x1 - x0) * (k / max(1, n - 1)); shown = e * (n - 1) + 0.05 >= k
        if not shown: continue
        d.ellipse([px - H * 0.014, y - H * 0.011, px + H * 0.014, y + H * 0.019], fill=(255, 255, 255, 255))
        up = k % 2 == 0; ty = y - H * 0.19 if up else y + H * 0.06
        tw = d.textlength(x["t"], font=big); d.text((min(max(px - tw / 2, W * 0.03), W * 0.97 - tw), ty), x["t"], font=big, fill=(255, 255, 255, 255))
        tx = x["text"]; sw = d.textlength(tx, font=small); d.text((min(max(px - sw / 2, W * 0.03), W * 0.97 - sw), ty + H * 0.085), tx, font=small, fill=(215, 225, 235, 255))

def _compare_frame(g, t, W, H, img, d, ov):
    e = 1 - (1 - min(1, t * 1.2)) ** 3; a, b = g["a"], g["b"]; hi = max(a["value"], b["value"]); lo = min(a["value"], b["value"])
    ratio = hi / lo; logscale = ratio > 20
    def frac(v): return (np.log10(v) - np.log10(lo) + 0.35) / (np.log10(hi) - np.log10(lo) + 0.35) if logscale else v / hi
    lab = font(int(H * 0.05)); big = font(int(H * 0.07)); small = font(int(H * 0.045), bold=False)
    d.text((W * 0.08, H * 0.12), str(g.get("label", "")).upper(), font=lab, fill=(120, 220, 255, 255))
    for k, (r, col) in enumerate(((a, (120, 220, 255, 255)), (b, (255, 190, 70, 255)))):
        y = H * (0.35 + 0.26 * k); wmax = W * 0.62 * frac(r["value"]) * e
        d.text((W * 0.1, y - H * 0.075), r["name"].upper(), font=small, fill=(230, 235, 240, 255))
        d.rectangle([W * 0.1, y, W * 0.1 + max(4, wmax), y + H * 0.07], fill=col)
        d.text((W * 0.1 + max(4, wmax) + W * 0.015, y + H * 0.004), _fmt(r["value"] * e, g.get("unit", "")), font=big, fill=(255, 255, 255, 255))
    if e > 0.9: d.text((W * 0.1, H * 0.86), f"{ratio:,.0f}x" if ratio >= 10 else f"{ratio:.1f}x", font=big, fill=(255, 255, 255, 255))

def graphic_frame(g, t, W, H, bg=None):
    """Counter + gauge bar (default), timeline or compare. Eased. t in 0..1. All drawn by code: a free shot type."""
    if g.get("kind") in ("timeline", "compare"):
        img = bg.copy() if bg is not None else Image.new("RGB", (W, H), (8, 12, 18))
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov); d.rectangle([0, 0, W, H], fill=(0, 0, 0, 150))
        (_timeline_frame if g["kind"] == "timeline" else _compare_frame)(g, t, W, H, img, d, ov)
        return Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
    e = 1 - (1 - min(1, t * 1.25)) ** 3
    img = bg.copy() if bg is not None else Image.new("RGB", (W, H), (8, 12, 18))
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    d.rectangle([0, 0, W, H], fill=(0, 0, 0, 140))
    try: a, b = float(g.get("from", 0)), float(g.get("to", 100))
    except Exception: a, b = 0.0, 100.0
    v = a + (b - a) * e
    big = font(int(H * 0.16)); small = font(int(H * 0.045), bold=False)
    txt = _fmt(v, g.get("unit", ""))
    tw = d.textlength(txt, font=big); d.text(((W - tw) / 2, H * 0.34), txt, font=big, fill=(255, 255, 255, 255))
    lab = str(g.get("label", ""))[:48].upper(); lw = d.textlength(lab, font=small)
    d.text(((W - lw) / 2, H * 0.25), lab, font=small, fill=(120, 220, 255, 255))
    x0, x1, y = W * 0.2, W * 0.8, H * 0.62
    d.rectangle([x0, y, x1, y + H * 0.012], fill=(255, 255, 255, 60))
    d.rectangle([x0, y, x0 + (x1 - x0) * e, y + H * 0.012], fill=(120, 220, 255, 255))
    return Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")

