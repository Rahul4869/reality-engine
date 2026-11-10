"""Hours engine: more watch hours without new videos (localised titles and descriptions, and related helpers). See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import json, re
from whatifs.core import S, log, store, iso, FAKE, scrub

LANG_NAMES = {"es": "Spanish", "pt": "Portuguese (Brazil)", "hi": "Hindi", "de": "German", "fr": "French", "id": "Indonesian", "ja": "Japanese", "ar": "Arabic", "it": "Italian"}

def _langs(): return [x.strip() for x in str(S("LOCALIZE_LANGS") or "").split(",") if x.strip() in LANG_NAMES]

def translate(title, description):
    """{lang: {title, description}} for LOCALIZE_LANGS. Titles keep the hook's punch (not word-for-word); <=100 chars; descriptions <=4500."""
    from whatifs.models import ask
    langs = _langs()
    if not langs: return {}
    sysm = ("You localize YouTube titles and descriptions for a science 'what if' channel. Keep the hook's punch and meaning (not word-for-word), "
            "keep numbers, keep links and chapter timestamps exactly, keep the AI-disclosure sentence. Return JSON only: {lang: {title, description}}.")
    out = ask("localize", sysm, json.dumps({"langs": {l: LANG_NAMES[l] for l in langs}, "title": title, "description": description[:4000]}, ensure_ascii=False),
              want_json=True, max_tokens=6000, fake_key="localize")
    res = {}
    for l in langs:
        v = (out or {}).get(l) if isinstance(out, dict) else None
        if isinstance(v, dict) and str(v.get("title") or "").strip():
            res[l] = {"title": str(v["title"]).strip()[:100], "description": str(v.get("description") or "").strip()[:4500]}
    return res

def apply(vid, loc):
    """Set localizations on a video. True when YouTube accepted them."""
    if not loc: return False
    if FAKE: return True
    import requests
    from whatifs.publish import YT, gheaders
    r = requests.get(YT + f"videos?part=snippet,localizations&id={vid}", headers=gheaders(), timeout=30).json()
    if not r.get("items"): return False
    it = r["items"][0]; sn = it["snippet"]
    body = {"id": vid, "snippet": {"title": sn["title"], "description": sn.get("description", ""), "categoryId": sn.get("categoryId", "27"),
                                   "tags": sn.get("tags", []), "defaultLanguage": sn.get("defaultLanguage") or "en"},
            "localizations": {**(it.get("localizations") or {}), **loc}}
    rr = requests.put(YT + "videos?part=snippet,localizations", headers=gheaders(), json=body, timeout=30)
    if rr.status_code >= 300: log(f"localizations not set ({rr.status_code}): {rr.text[:160]}", "WARN"); return False
    return True

def tick():
    """One long video per run: the newest uploaded one without localizations. Never raises."""
    if not S("LOCALIZATIONS_ON", bool) or not _langs(): return None
    try:
        st = store(); done = {r.get("yt_id") for r in st.rows("Localizations")}
        eps = [e for e in st.rows("Episodes") if e.get("yt_id") and e.get("yt_id") not in done and str(e.get("status", "")).upper() not in ("KILLED", "FAILED")]
        if not eps: return None
        e = sorted(eps, key=lambda x: str(x.get("slot_et", "")))[-1]
        from whatifs.publish import yt_status_full
        title = str(e.get("title") or "")
        desc = ""
        if not FAKE:
            import requests
            from whatifs.publish import YT, gheaders
            it = requests.get(YT + f"videos?part=snippet&id={e['yt_id']}", headers=gheaders(), timeout=30).json().get("items") or []
            if it: title, desc = it[0]["snippet"]["title"], it[0]["snippet"].get("description", "")
        loc = translate(title, desc)
        ok = apply(e["yt_id"], loc)
        st.append("Localizations", [{"ts": iso(), "episode_id": e.get("episode_id"), "yt_id": e["yt_id"], "langs": ",".join(sorted(loc)), "ok": "TRUE" if ok else "FALSE"}])
        log(f"localizations {'set' if ok else 'not set'} for {e.get('episode_id')} ({len(loc)} languages)"); return ok
    except Exception as x:
        log(f"localizations skipped: {scrub(x)}", "WARN"); return None

def affiliate_block(premise_text=""):
    """The description block: one topic-matched affiliate link + the disclosure. '' when off or no links."""
    if not S("AFFILIATE_ON", bool): return ""
    try: links = json.loads(S("AFFILIATE_LINKS") or "[]")
    except Exception: return ""
    links = [l for l in links if isinstance(l, dict) and str(l.get("url", "")).startswith("https://")]
    if not links: return ""
    words = set(re.findall(r"[a-z]{4,}", str(premise_text).lower()))
    best = max(links, key=lambda l: len(words & set(str(t).lower() for t in (l.get("topics") or []))))
    line = str(best.get("line") or f"Learn the science behind this with {best.get('name', 'this course')}").strip()
    return f"{line}: {best['url']}\n{S('AFFILIATE_DISCLOSURE')}"
