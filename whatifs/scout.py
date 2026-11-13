"""The weekly tool scout: new models, prices and deprecations from the fal catalog and Artificial Analysis. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
from whatifs.core import S, log, store, iso, now_utc, set_setting, env, FAKE, scrub

FAL = "https://api.fal.ai/v1"
AA = "https://artificialanalysis.ai/api/v2"

def used_endpoints():
    ids = {str(S(k) or "").strip() for k in ("FAL_HERO_MODEL", "FAL_LIVING_MODEL", "FAL_IMAGE_MODEL") if str(S(k) or "").strip()}
    return sorted(i for i in ids if "/" in i)

def _get(url, params=None, headers=None):
    import requests
    r = requests.get(url, params=params, headers=headers or {}, timeout=30); r.raise_for_status(); return r.json()

def fal_catalog(category="image-to-video"):
    if FAKE:
        return [{"endpoint_id": "fal-ai/newvid/v1/image-to-video", "metadata": {"display_name": "NewVid 1", "status": "active", "date": "2026-11-08"}}]
    h = {"Authorization": f"Key {env('FAL_KEY')}"} if env("FAL_KEY") else {}
    out, params = [], {"category": category, "status": "active", "sort": "recent", "limit": 50}
    for _ in range(3):                                                        # newest first; 3 pages is plenty weekly
        j = _get(f"{FAL}/models", params, h); out += j.get("models", [])
        if not j.get("has_more"): break
        params["cursor"] = j["next_cursor"]
    return out

def fal_status(ids):
    if FAKE: return {i: "active" for i in ids}
    h = {"Authorization": f"Key {env('FAL_KEY')}"} if env("FAL_KEY") else {}
    j = _get(f"{FAL}/models", [("endpoint_id", i) for i in ids], h)
    got = {m["endpoint_id"]: (m.get("metadata") or {}).get("status", "active") for m in j.get("models", [])}
    return {i: got.get(i, "missing") for i in ids}

def fal_licence(ids):
    """{model id: the licence word of fal's own listing ("commercial", "research", ...)} - free, no key needed. v12 V2d-b: read live, because a model
    the code paid was licensed for research only. Offline: what each model's own row says."""
    if FAKE:
        from whatifs import clips as CL
        return {i: str((CL.row(i) or {}).get("lic") or "") for i in ids}
    h = {"Authorization": f"Key {env('FAL_KEY')}"} if env("FAL_KEY") else {}
    j = _get(f"{FAL}/models", [("endpoint_id", i) for i in ids], h)
    return {m["endpoint_id"]: str(m.get("license_type") or (m.get("metadata") or {}).get("license_type") or "") for m in j.get("models", [])}

def fal_prices(ids):
    if not ids: return {}
    if FAKE: return {i: {"unit_price": 0.07, "unit": "second", "currency": "USD"} for i in ids}
    h = {"Authorization": f"Key {env('FAL_KEY')}"}
    return {p["endpoint_id"]: p for p in _get(f"{FAL}/models/pricing", [("endpoint_id", i) for i in ids[:50]], h).get("prices", [])}

def fal_schema(endpoint_id):
    """The model's whole OpenAPI document from fal's listing (no key needed), or None when the listing has none. Offline: a document that says what
    the model's own row in CLIP_MODELS says (nothing is proven offline; the tests hand in their own documents)."""
    if FAKE:
        from whatifs import clips as CL
        r = CL.row(endpoint_id) or {}; props = {"prompt": {"type": "string"}, str(r.get("start") or "image_url"): {"type": "string"},
                                                "duration": {"type": "integer", "minimum": int(r.get("min_s") or 5), "maximum": int(r.get("max_s") or 5)}}
        if r.get("res_field"): props[str(r["res_field"])] = {"type": "string", "enum": list((r.get("usd_s") or {}).keys())}
        return {"components": {"schemas": {"Input": {"properties": props}}}}
    h = {"Authorization": f"Key {env('FAL_KEY')}"} if env("FAL_KEY") else {}
    j = _get(f"{FAL}/models", [("endpoint_id", endpoint_id), ("expand", "openapi-3.0")], h)
    doc = next(((m.get("openapi") or None) for m in j.get("models", []) if m.get("endpoint_id") == endpoint_id), None)
    return None if not isinstance(doc, dict) or doc.get("error") else doc

def aa_ranking():
    key = env("AA_API_KEY")
    if FAKE or not key: return {}
    j = _get(f"{AA}/media/image-to-video/models/free", headers={"x-api-key": key})
    return {str(m.get("name", "")).lower(): m.get("elo") for m in j.get("data", [])}

def weekly(now=None):
    now = now or now_utc()
    if not S("SCOUT_ON", bool) or str(S("SCOUT_LAST") or "")[:10] == now.strftime("%Y-%m-%d") or now.weekday() != S("SCOUT_WEEKDAY", int): return {}
    set_setting("SCOUT_LAST", iso(now)); res = {"new": [], "deprecated": []}
    try:
        st = store(); seen = {r.get("endpoint_id") for r in st.rows("Tool_Scout")}
        for i, s in fal_status(used_endpoints()).items():
            if s != "active": res["deprecated"].append((i, s))
        if res["deprecated"]:
            from whatifs import notify as NT
            NT.send("scout_deprecated", "URGENT: a model the pipeline uses is " + ", ".join(f"{i} ({s})" for i, s in res["deprecated"])
                    + ". The Steward will fall back down the ladder; tell me if you want a replacement chosen now.",
                    [("OK", "OK")], tier="now", urgent=True, default="ok", expires_h=72, dedupe_key="dep|" + ",".join(i for i, _ in res["deprecated"]))
        from whatifs import clips as CL
        if CL.on():                                                            # v12 V2d: the listing's price is a BASE figure, wrong for our setting in four of five models read on 13 Nov 2026 -
            res["clips"] = CL.review(now)                                      # it is watched (a move marks the row stale and tells the owner) and never written into the estimate
        hero = str(S("FAL_HERO_MODEL") or "")                                 # v11: the real price of our animated-scene model, from fal's pricing API
        p = fal_prices([hero]).get(hero) if (hero and not CL.on()) else None
        if p and str(p.get("unit", "")).lower().startswith("second"):
            real5 = round(float(p["unit_price"]) * 5, 4); cur = S("PRICE_KLING_USD", float)
            res["price_check"] = {"model": hero, "usd_per_5s": real5, "was": cur}
            if cur <= 0 or abs(real5 - cur) / cur > 0.10:
                set_setting("PRICE_KLING_USD", str(real5))
                from whatifs import notify as NT
                NT.send("scout_price", f"Price update: {hero} now costs ${real5:.3f} per 5-second scene (the cost model said ${cur:.3f}). The budget plan now uses "
                        "the real price.", [("OK", "OK")], tier="digest", default="ok", expires_h=72, dedupe_key=f"price|{hero}|{real5}")
        cat = [m for m in fal_catalog() if m.get("endpoint_id") not in seen]
        prices = fal_prices([m["endpoint_id"] for m in cat]); aa = aa_ranking()
        for m in cat:
            md = m.get("metadata") or {}; p = prices.get(m["endpoint_id"], {})
            elo = next((v for k, v in aa.items() if k and k in str(md.get("display_name", "")).lower()), "")
            st.append("Tool_Scout", [{"ts": iso(now), "endpoint_id": m["endpoint_id"], "name": md.get("display_name", ""), "category": "image-to-video",
                                      "unit_price": p.get("unit_price", ""), "unit": p.get("unit", ""), "aa_elo": elo,
                                      "note": "Data: Artificial Analysis" if elo else ""}])
            res["new"].append(m["endpoint_id"])
        if res["new"]: log(f"tool scout: {len(res['new'])} new image-to-video model(s) logged in Tool_Scout")
    except Exception as e: log(f"tool scout skipped: {scrub(e)[:160]}", "WARN")
    return res
