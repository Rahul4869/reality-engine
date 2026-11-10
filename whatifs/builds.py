"""Owner builds and repairs through Claude Code in GitHub Actions (claude-build workflow) and the Merge / Reject / auto-merge rules. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import os, json
from whatifs.core import S, log, env, iso, store, scrub, FAKE

API = "https://api.github.com"

def _h():
    tok = env("GH_MERGE_TOKEN") or env("GH_ACTIONS_TOKEN") or env("GH_TOKEN")      # v11.1: the tick's own token (actions: write only)
    return {"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}

def dispatch(workflow, inputs, ref="main"):
    """Start a workflow (workflow_dispatch). Returns True when GitHub accepted it."""
    if FAKE: log(f"FAKE dispatch {workflow} {json.dumps(inputs)[:120]}"); return True
    import requests
    r = requests.post(f"{API}/repos/{env('GH_REPO')}/actions/workflows/{workflow}/dispatches", headers=_h(), json={"ref": ref, "inputs": inputs}, timeout=30)
    if r.status_code >= 300: log(f"dispatch {workflow} failed {r.status_code}: {r.text[:160]}", "WARN"); return False
    return True

def request_build(spec, kind="tweak"):
    """An owner-ordered change (kind tweak|feature) or a repair. Returns True when the build workflow was started."""
    if not S("BUILDS_ON", bool): log("builds are switched off (BUILDS_ON)"); return False
    return dispatch("claude-build.yml", {"spec": str(spec)[:6000], "kind": kind if kind in ("tweak", "feature", "repair") else "tweak"})

def pr_state(n):
    """{'mergeable', 'checks': 'green|red|pending', 'merged', 'head'} for pull request n (FAKE: green)."""
    if FAKE: return {"mergeable": True, "checks": "green", "merged": False, "head": "fake"}
    import requests
    repo = env("GH_REPO"); pr = requests.get(f"{API}/repos/{repo}/pulls/{n}", headers=_h(), timeout=30).json()
    sha = (pr.get("head") or {}).get("sha", "")
    runs = requests.get(f"{API}/repos/{repo}/commits/{sha}/check-runs", headers=_h(), timeout=30).json().get("check_runs", []) if sha else []
    if not runs: checks = "pending"
    elif all(r.get("status") == "completed" for r in runs): checks = "green" if all(r.get("conclusion") in ("success", "skipped", "neutral") for r in runs) else "red"
    else: checks = "pending"
    return {"mergeable": pr.get("mergeable"), "checks": checks, "merged": bool(pr.get("merged")), "head": sha}

def merge_pr(n, why="owner"):
    """Squash-merge pull request n when every check is green. Returns (ok, message)."""
    st = pr_state(n)
    if st.get("merged"): return True, f"#{n} was already merged"
    if st.get("checks") != "green": return False, f"#{n} not merged: checks are {st.get('checks')}"
    if FAKE: log(f"FAKE merge #{n} ({why})"); return True, f"merged #{n} (fake)"
    import requests
    r = requests.put(f"{API}/repos/{env('GH_REPO')}/pulls/{n}/merge", headers=_h(), json={"merge_method": "squash"}, timeout=30)
    if r.status_code >= 300: return False, f"#{n} not merged: GitHub said {r.status_code} {r.text[:120]}"
    log(f"merged #{n} ({why}); the next Pipeline run uses the new code"); return True, f"merged #{n}"

def close_pr(n):
    if FAKE: return True
    import requests
    r = requests.patch(f"{API}/repos/{env('GH_REPO')}/pulls/{n}", headers=_h(), json={"state": "closed"}, timeout=30)
    return r.status_code < 300

def _on_answer(row, choice):
    n = str(row.get("text_ref") or "").strip() or _pr_of(row)
    c = str(choice).upper()
    if c.startswith("MERGE"): ok, msg = merge_pr(n, "owner tap"); return msg
    if c.startswith("REJECT"): return f"closed #{n}" if close_pr(n) else f"could not close #{n}"
    return "recorded"

def _pr_of(row):
    import re
    m = re.search(r"#(\d+)", str(row.get("text") or "")); return m.group(1) if m else ""

def _on_default(row):
    """Decision 11: a TWEAK the owner ordered merges by itself 24 h after every check is green; features and repairs only wait."""
    if str(row.get("default_action") or "").startswith("auto-merge"):
        ok, msg = merge_pr(_pr_of(row), "auto-merge after 24 h green (decision 11)"); log(msg)

def build_ready(pr, kind, branch=""):
    """Called by claude-build.yml once the pull request exists: one owner message with Merge / Reject (notify, 'now' tier)."""
    from whatifs import notify as NT
    NT.register("build_ready", on_answer=_on_answer, on_default=_on_default)
    tweak = kind == "tweak" and S("AUTO_MERGE_TWEAKS_ON", bool)
    text = f"Change #{pr} ({kind}) is built and its checks are running. " + ("It merges by itself 24 h after every check is green unless you stop it." if tweak else "Tap Merge when you want it live.")
    return NT.send("build_ready", text, [("Merge", f"MERGE #{pr}"), ("Reject", f"REJECT #{pr}")], tier="now", urgent=False,
                   default="auto-merge after 24 h green" if tweak else "waits; expires after 7 days", expires_h=24 if tweak else 24 * 7, dedupe_key=f"build|{pr}")

NT_REGISTERED = False
def ensure_registered():
    global NT_REGISTERED
    if not NT_REGISTERED:
        from whatifs import notify as NT
        NT.register("build_ready", on_answer=_on_answer, on_default=_on_default); NT_REGISTERED = True
