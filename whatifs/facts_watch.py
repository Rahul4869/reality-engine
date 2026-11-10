"""Platform Facts watcher: weekly fingerprint of the official change-log pages; a change sends the owner one message (no AI call). See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import hashlib, json, re
from whatifs.core import S, log, set_setting, now_utc, FAKE

def _text(html):
    t = re.sub(r"(?is)<(script|style|nav|footer|header)[^>]*>.*?</\1>", " ", html or "")
    t = re.sub(r"(?s)<[^>]+>", " ", t); t = re.sub(r"\s+", " ", t)
    return t.strip()[:60000]

def _fetch(url):
    import requests
    r = requests.get(url, timeout=25, headers={"User-Agent": "RealityEngine-facts-watch/1.0"})
    r.raise_for_status(); return _text(r.text)

def run(fetch=None):
    """Returns the list of changed URLs (cards created). fetch(url)->text can be injected (tests)."""
    if not S("FACTS_WATCH_ON", bool) or (FAKE and fetch is None): return []
    fetch = fetch or _fetch
    try: state = json.loads(S("FACTS_WATCH_STATE") or "{}")
    except Exception: state = {}
    changed = []
    for url in [u.strip() for u in str(S("FACTS_WATCH_URLS") or "").split(",") if u.strip()]:
        try: txt = fetch(url)
        except Exception as e: log(f"facts watch: {url} not read ({str(e)[:80]})", "WARN"); continue
        h = hashlib.sha256(txt.encode("utf-8", "ignore")).hexdigest()[:20]
        old = state.get(url, {})
        if old.get("hash") and old["hash"] != h: changed.append(url)
        state[url] = {"hash": h, "checked": now_utc().strftime("%Y-%m-%d")}
    set_setting("FACTS_WATCH_STATE", json.dumps(state))
    if changed:
        from whatifs import notify as NT
        for url in changed:
            NT.send("platform_change", f"A platform page changed: <a href='{url}'>{url}</a>. Ask the build chat (or the dashboard chat) to read it and say whether anything must change.",
                    [("Discuss", "DISCUSS facts"), ("Noted", "NOTED")], tier="week", default="noted", expires_h=24 * 7, dedupe_key=f"facts|{url}|{now_utc():%G-W%V}")
    log(f"facts watch: {len(state)} page(s) checked, {len(changed)} changed"); return changed
