"""Charts as PNG images for WhatsApp and the digests (real numbers only; no data = no chart). See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import os
from whatifs.core import WORK

def _font(n, bold=True):
    from whatifs.media import font
    return font(n, bold=bold)

def bars(values, labels, title, source, path, demo=False, unit=""):
    """A clean bar chart (1080x1080, readable on a phone). values: numbers; labels: short strings."""
    vals = [float(v) for v in values if v is not None]
    if not vals: return None
    from PIL import Image, ImageDraw
    W = H = 1080; im = Image.new("RGB", (W, H), (14, 15, 20)); d = ImageDraw.Draw(im)
    d.text((48, 40), title, font=_font(46), fill=(255, 214, 0))
    if demo: d.text((W - 260, 48), "DEMO DATA", font=_font(34), fill=(255, 80, 80))
    top, base, left, right = 160, 860, 70, W - 40
    mx = max(vals) or 1.0; n = len(vals); bw = (right - left) / max(1, n)
    for i, v in enumerate(vals):
        x0 = left + i * bw + bw * 0.15; x1 = left + (i + 1) * bw - bw * 0.15; h = (base - top) * (v / mx)
        d.rectangle([x0, base - h, x1, base], fill=(108, 255, 90) if i == n - 1 else (90, 140, 200))
        txt = f"{v:,.0f}{unit}" if v >= 100 else f"{v:.1f}{unit}"
        d.text((x0, base - h - 44), txt, font=_font(30), fill=(240, 240, 245))
        lab = str(labels[i] if i < len(labels) else "")[:14]
        d.text((x0, base + 14), lab, font=_font(24, bold=False), fill=(200, 200, 210))
    d.line([left, base, right, base], fill=(80, 80, 90), width=3)
    d.text((48, H - 70), f"Source: {source}"[:80], font=_font(26, bold=False), fill=(170, 170, 180))
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True); im.save(path, "PNG"); return path

def numbers_chart(view, path=None):
    vids = ((view.get("numbers") or {}).get("videos") or [])[-6:]
    if not vids: return None
    path = path or os.path.join(WORK, "charts", "numbers.png")
    return bars([v.get("views") for v in vids], [v.get("title", "")[:14] for v in vids], "Views per video", "YouTube Analytics (Analytics tab)", path, demo=bool(view.get("demo")))

def money_chart(view, path=None):
    m = view.get("money") or {}
    if m.get("month_spend") is None: return None
    path = path or os.path.join(WORK, "charts", "money.png")
    return bars([m.get("month_spend"), m.get("cap")], ["spent", "cap"], "This month (Rs)", "Cost_Log", path, demo=bool(view.get("demo")))
