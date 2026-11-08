"""v10.1 (K149): Instagram "Case Files" carousel per long episode (saves + sends are Instagram's strongest growth signals). At production
time 6 slides (1080x1350 JPEG, 4:5) are made from the episode's own stills + the show plan (case, exhibits, objection, no verdict spoiler,
'full trial: link in bio' + subscribe) and kept privately on Drive. When the long video goes live, the slides are put on the dashboard Worker
as short-lived public JPEGs (KV 'pub:<32 hex>' with a 1-day TTL; Meta fetches image_url) and published as one carousel
(children <= 20, is_ai_generated on the PARENT only; verified 8 Nov 2026). At most CAROUSEL_PER_WEEK; ₹0 (pictures already paid)."""
from __future__ import annotations
import glob, json, os, secrets
from whatifs.core import S, log, store, iso, now_utc, parse_iso, env, FAKE, WORK, scrub

W, H = 1080, 1350

def _pick_stills(ep, n=5):
    files = [f for f in glob.glob(os.path.join(WORK, ep, "**", "*"), recursive=True) if f.lower().endswith((".png", ".jpg", ".jpeg"))
             and "thumb" not in os.path.basename(f).lower() and os.path.getsize(f) > 20_000]
    files.sort(key=lambda f: -os.path.getsize(f))
    step = max(1, len(files) // max(1, n)); out = files[::step][:n]
    return out

def _slide(img_path, title, sub, out):
    from PIL import Image, ImageDraw, ImageFilter
    from whatifs.specials import _wrap
    from whatifs.media import font
    im = Image.open(img_path).convert("RGB") if img_path else Image.new("RGB", (W, H), (20, 22, 40))
    r = max(W / im.width, H / im.height); im = im.resize((int(im.width * r) + 1, int(im.height * r) + 1))
    x, y = (im.width - W) // 2, (im.height - H) // 2; im = im.crop((x, y, x + W, y + H))
    shade = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d0 = ImageDraw.Draw(shade)
    for i in range(H // 2): d0.line([(0, H - i), (W, H - i)], fill=(0, 0, 0, int(200 * (1 - i / (H / 2)))))
    im = Image.alpha_composite(im.convert("RGBA"), shade).convert("RGB"); d = ImageDraw.Draw(im)
    f1, f2 = font(64), font(40, bold=False); y = int(H * 0.62)
    for txt, f, col in ((title, f1, (255, 214, 0)), (sub, f2, (240, 240, 245))):
        for line in _wrap(d, txt, f, int(W * 0.86))[:4]:
            w = d.textlength(line, font=f); d.text(((W - w) / 2 + 2, y + 2), line, font=f, fill=(0, 0, 0)); d.text(((W - w) / 2, y), line, font=f, fill=col); y += int(f.size * 1.25)
        y += 12
    im.save(out, "JPEG", quality=90); return out

def prepare(ep, plan, title):
    """Production job: make the slides, keep them privately on Drive, record READY. Never raises."""
    if not S("CAROUSEL_ON", bool): return None
    try:
        from whatifs import publish as PUB
        stills = _pick_stills(ep); ex = [x for x in (plan or {}).get("exhibits", []) if isinstance(x, dict)][:4]
        texts = [(f"CASE FILE: {str(title)[:60]}", str((plan or {}).get("charge") or "Reality is on trial")[:120])]
        for i, x in enumerate(ex):
            texts.append((f"EXHIBIT {x.get('id', chr(65 + i))}", str(x.get("what") or "")[:140] + (f"  Grimm: \"{str(x.get('objection'))[:90]}\"" if x.get("objection") else "")))
        texts.append(("THE VERDICT?", "Watch the full trial: link in bio. Take your seat on the jury: follow."))
        os.makedirs(os.path.join(WORK, ep, "carousel"), exist_ok=True); fids = []
        for i, (a, b) in enumerate(texts[:6]):
            p = _slide(stills[i % len(stills)] if stills else None, a, b, os.path.join(WORK, ep, "carousel", f"slide{i + 1}.jpg"))
            fid, _url = PUB.drive_upload(p, f"{ep}_slide{i + 1}.jpg", public=False); fids.append(fid)
        cap = f"{str(title)[:120]}\nCase files from today's trial. Which exhibit convinced you? Send this to your co-juror.\nFull trial: link in bio. AI-assisted visuals; original story."
        store().append("Carousels", [{"ts": iso(), "episode_id": ep, "files": ",".join(fids), "caption": cap[:2000], "status": "READY", "ig_id": ""}])
        return fids
    except Exception as e:
        log(f"carousel not prepared: {scrub(e)[:160]}", "WARN", ep); return None

def _public_url(fid, ep):
    """A short-lived public JPEG on the Worker (preferred), else a public Drive link."""
    from whatifs import publish as PUB
    base, acc, ns, tok = str(S("WORKER_PUBLIC_URL") or "").rstrip("/"), env("CF_ACCOUNT_ID"), env("CF_KV_NAMESPACE_ID"), env("CF_KV_TOKEN")
    if base and acc and ns and tok and not FAKE:
        import requests
        path = os.path.join(WORK, ep, "carousel", f"{fid}.jpg"); os.makedirs(os.path.dirname(path), exist_ok=True)
        PUB.drive_download(fid, path); key = secrets.token_hex(16)
        r = requests.put(f"https://api.cloudflare.com/client/v4/accounts/{acc}/storage/kv/namespaces/{ns}/values/pub:{key}",
                         params={"expiration_ttl": 86400}, headers={"Authorization": f"Bearer {tok}", "Content-Type": "image/jpeg"}, data=open(path, "rb").read(), timeout=60)
        if r.status_code < 300: return f"{base}/pub/{key}.jpg", None
    fid2, url = PUB.drive_upload(os.path.join(WORK, ep, "carousel", f"{fid}.jpg"), f"{fid}.jpg", public=True) if not FAKE else (fid, f"https://example.invalid/{fid}.jpg")
    return url, fid2

def post(ep):
    """Release job: publish the READY carousel of this episode (at most CAROUSEL_PER_WEEK). Never raises."""
    if not S("CAROUSEL_ON", bool): return None
    st = store(); row = next((r for r in st.rows("Carousels") if r.get("episode_id") == ep and r.get("status") == "READY"), None)
    if not row: return None
    week = [r for r in st.rows("Carousels") if r.get("status") == "POSTED" and parse_iso(r.get("ts")) and (now_utc() - parse_iso(r.get("ts"))).days < 7]
    if len(week) >= S("CAROUSEL_PER_WEEK", int):
        st.update("Carousels", "episode_id", ep, {"status": "SKIPPED (weekly cap)"}); return None
    if FAKE:
        st.update("Carousels", "episode_id", ep, {"status": "POSTED", "ig_id": "FAKE_CAROUSEL"}); return "FAKE_CAROUSEL"
    from whatifs import publish as PUB
    import requests
    opened = []
    try:
        ig = S("IG_USER_ID"); kids = []
        for fid in [x for x in str(row.get("files") or "").split(",") if x][:20]:
            url, opened_fid = _public_url(fid, ep)
            if opened_fid: opened.append(opened_fid)
            c = requests.post(PUB.gv() + f"{ig}/media", headers=PUB.MH(), data={"image_url": url, "is_carousel_item": "true"}, timeout=60).json()
            if "id" not in c: raise RuntimeError(f"carousel item: {str(c)[:160]}")
            kids.append(c["id"])
        data = {"media_type": "CAROUSEL", "children": ",".join(kids), "caption": row.get("caption", "")}
        if S("META_AI_LABEL_ON", bool): data["is_ai_generated"] = "true"      # the parent only (children error)
        p = requests.post(PUB.gv() + f"{ig}/media", headers=PUB.MH(), data=data, timeout=60).json()
        if "id" not in p: raise RuntimeError(f"carousel parent: {str(p)[:160]}")
        mid = PUB._ig_finish(ig, p["id"])
        st.update("Carousels", "episode_id", ep, {"status": "POSTED", "ig_id": str(mid)}); return mid
    except Exception as e:
        st.update("Carousels", "episode_id", ep, {"status": f"FAILED: {scrub(e)[:120]}"}); log(f"carousel not posted: {scrub(e)[:160]}", "WARN", ep); return None
    finally:
        for f in opened:
            try: PUB.drive_private(f)
            except Exception: pass
