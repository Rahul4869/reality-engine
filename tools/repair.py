"""Repair bot: on a crashed job, sends the traceback and the failing file to the model, checks the fixed file with Plan Guard and the offline rehearsal, and opens a pull request. See docs/CURRENT/SYSTEM.md."""
import os, re, sys, subprocess, json, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from whatifs import prompts as P

SECRET_ENVS = ("G_CLIENT_ID", "G_CLIENT_KEY", "G_REFRESH", "G_REFRESH_DRIVE", "ANTHROPIC_KEY", "GEMINI_KEY", "FAL_KEY", "PEXELS_KEY", "META_PAGE_KEY",
               "SHEET_ID", "GH_TOKEN", "GITHUB_TOKEN", "OWNER_EMAIL")
# v8.3: files that guard money, quality and publishing are NEVER merged automatically, whatever the setting says: the owner (or Claude, with the owner) reads the change first.
PROTECTED = ("whatifs/qc.py", "whatifs/governor.py", "whatifs/fixes.py", "whatifs/publish.py", "whatifs/episode.py", "whatifs/core.py", "whatifs/models.py",
             "whatifs/checkpoint.py", "whatifs/preflight.py", "whatifs/manage.py", "tools/plan_guard.py", "tools/repair.py", "whatifs/playbook.py",
             "whatifs/tts_gemini.py", "whatifs/premise.py", "whatifs/craft.py", "whatifs/preview.py",
             "whatifs/immersion.py", "whatifs/room.py",
             "whatifs/org/palace.py", "whatifs/org/schemas.py", "whatifs/org/memos.py", "whatifs/org/registry.py", "whatifs/org/runner.py", "whatifs/org/wraps.py",
             "whatifs/org/levers.py", "whatifs/org/execute.py", "whatifs/builds.py", "whatifs/org/rnd.py", "whatifs/org/board.py", "whatifs/org/cite.py", "whatifs/org/canon.py", "whatifs/org/audience.py", "whatifs/org/inside.py", "whatifs/path.py", "whatifs/org/layman.py", "whatifs/formats.py", "whatifs/org/shortseat.py", "whatifs/shorts2.py",
             "whatifs/contract.py", "whatifs/truth.py", "whatifs/ladder.py", "whatifs/release.py", "whatifs/opening.py", "whatifs/clips.py", "whatifs/costguard.py", "whatifs/motion.py", "whatifs/stock.py")      # v8.11: Kling placement and the model routing / ship-the-best gates      # v8.10: the new paid call (TTS) and the new quality gates
RISKY = [r"\brequests\.", r"\burllib", r"\bsocket\b", r"\bhttp\.client", r"os\.environ", r"\benv\(", r"\bsubprocess\b", r"os\.system",
         r"\beval\(", r"\bexec\(", r"__import__", r"shutil\.rmtree", r"os\.remove", r"https?://", r"base64", r"pickle"]

def _setting(key, default):
    """Read a Settings-tab cell (needs the Sheet keys); falls back to the env/default if the Sheet can't be read."""
    try:
        if os.environ.get("SHEET_ID"):
            from whatifs.core import S
            v = str(S(key)).strip()
            if v: return v
    except Exception as e: print("settings read failed:", str(e)[:120])
    return os.environ.get(key, default)

def _new_risky(old, new):
    """Patterns that appear more often in the fixed file than in the original = new reach to network/keys/shell."""
    return [p for p in RISKY if len(re.findall(p, new)) > len(re.findall(p, old))]

def _clean_env(**extra):
    e = {k: v for k, v in os.environ.items() if k not in SECRET_ENVS}
    e.update(extra); return e

def _recent_repairs(days=7):
    try:
        out = subprocess.run(["gh", "pr", "list", "--state", "all", "--search", "Repair in:title", "--json", "createdAt", "--limit", "50"],
                             capture_output=True, text=True).stdout
        import datetime as dt
        cut = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None) - dt.timedelta(days=days)
        return sum(1 for x in json.loads(out or "[]") if dt.datetime.strptime(x["createdAt"][:19], "%Y-%m-%dT%H:%M:%S") > cut)
    except Exception: return 0

def _same_error_recently(sig):
    try:
        out = subprocess.run(["gh", "pr", "list", "--state", "all", "--search", sig + " in:body", "--json", "number", "--limit", "5"], capture_output=True, text=True).stdout
        return len(json.loads(out or "[]")) > 0
    except Exception: return False

def main():
    err = open("last_error.txt").read() if os.path.exists("last_error.txt") else sys.stdin.read()
    from whatifs.core import scrub
    err = scrub(err)
    import hashlib
    sig = "sig" + hashlib.md5(re.sub(r"\d+", "", err[-600:]).encode()).hexdigest()[:10]
    try: cap = int(float(_setting("MAX_REPAIRS_PER_WEEK", os.environ.get("MAX_REPAIRS", "3"))))
    except Exception: cap = 3
    if _recent_repairs() >= cap:
        print(f"repair cap reached ({cap}/week) - skipping. Owner gets one email from the pipeline."); return 0
    if _same_error_recently(sig):
        print("this exact error was already attempted - skipping to avoid loops"); return 0
    files = re.findall(r'File "([^"]*?/(?:whatifs|tools)/[^"]+\.py)"', err)
    if not files: print("no repo file in traceback"); return 0
    rel = files[-1].split("/repo/")[-1] if "/repo/" in files[-1] else re.sub(r"^.*?/((?:whatifs|tools)/.*)$", r"\1", files[-1])
    if not os.path.exists(rel): print("file not found", rel); return 0
    src = open(rel).read()
    if str(_setting("REPAIR_ENGINE", "claude_code")).strip().lower() == "claude_code":          # v9.4a (WP3): Claude Code repairs on the owner's plan
        from whatifs.builds import request_build
        spec = (f"REPAIR. The workflow failed with this traceback (last 4000 chars):\n{err[-4000:]}\nFile most likely at fault: {rel}. Fix the root cause, keep every "
                f"K-rule, add a test that would have caught it. Put this tag in the pull request body so the same error is never attempted twice: {sig}")
        if request_build(spec, "repair"):
            print("repair handed to Claude Code (claude-build.yml)"); return 0
        print("Claude Code repair could not be started; falling back to the API repair")
    from whatifs.models import ask
    try:
        fixed = ask("repair", P.fill(P.REPAIR, path=rel, error=err[-6000:], file=src), "Return the full corrected file only.", want_json=False, max_tokens=32000, temperature=0)
    finally:
        try:
            from whatifs.core import flush_costs, flush_log; flush_costs(); flush_log()        # v8.3: the repair's own spend is written to Cost_Log
        except Exception as e: print("cost flush failed:", str(e)[:120])
    fixed = re.sub(r"^```(?:python)?\s*|\s*```$", "", fixed.strip(), flags=re.S) + "\n"
    if len(fixed) < len(src) * 0.6: print("repair too short, refused"); return 1
    br = f"repair-{int(time.time())}"
    subprocess.run(["git", "checkout", "-b", br], check=True)
    open(rel, "w").write(fixed)
    g = subprocess.run([sys.executable, "tools/plan_guard.py"], env=_clean_env()).returncode
    t = subprocess.run([sys.executable, "-m", "whatifs.cli", "rehearsal"], env=_clean_env(WI_FAKE="1", WI_SMALL="1", WI_WORK="rh")).returncode
    u = subprocess.run([sys.executable, "-m", "pytest", "tests", "-q"], env=_clean_env(WI_WORK="rh_tests")).returncode if os.path.isdir("tests") else 0   # v8.0: unit tests too
    if g or t or u: print("repair did not pass tests; discarded"); return 1
    subprocess.run(["git", "-c", "user.name=repair-bot", "-c", "user.email=bot@users.noreply.github.com", "commit", "-am", f"repair: {rel}"], check=True)
    subprocess.run(["git", "push", "origin", br], check=True)
    subprocess.run(["gh", "pr", "create", "--title", f"Repair {rel}", "--body", "Automatic repair. Plan Guard + unit tests + rehearsal passed. " + sig + "\n\nLast error line: `" + (err.strip().splitlines() or [""])[-1][:160].replace("`", "'") + "`", "--head", br], check=True)
    risky = _new_risky(src, fixed)
    auto = _setting("AUTO_MERGE_REPAIRS", os.environ.get("AUTO_MERGE", "TRUE")).upper() in ("TRUE", "YES", "1", "ON")
    protected = rel.replace("\\", "/") in PROTECTED
    if auto and not risky and not protected:
        subprocess.run(["gh", "pr", "merge", br, "--squash", "--delete-branch"], check=False)
    else:
        why = ("the fix adds new network/key/shell code: " + ", ".join(risky)) if risky else ("this file guards money, quality or publishing, so it is never merged automatically" if protected else "AUTO_MERGE_REPAIRS is FALSE")
        print("not auto-merged:", why)
        subprocess.run(["gh", "pr", "comment", br, "--body", "Waiting for the owner: " + why + ". Open Files changed, then Merge if it looks right (or ask Claude)."], check=False)
        try:
            from whatifs.publish import email
            email("A code repair is waiting for you", f"<p>The Repair Bot fixed <b>{rel}</b> and all tests passed, but it was not merged automatically because {why}.</p>"
                  "<p>Open the repo, Pull requests tab, read it (or paste it to Claude), then press Merge. Nothing else is needed.</p>")
        except Exception as e: print("email failed:", str(e)[:120])
    return 0

if __name__ == "__main__":
    sys.exit(main())

