"""CI report: turns the unit-test or rehearsal log of GitHub's Checks into annotations on the run page (readable without a sign-in), so a red run names its cause and a green run shows its totals and the rehearsal's episode id. See docs/CURRENT/SYSTEM.md."""
import os, re, sys

MAX_ERRORS = 8          # GitHub shows at most 10 annotations of one level per step: 8 causes + "and N more" + the totals line
ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
try:
    if ROOT not in sys.path: sys.path.insert(0, ROOT)
    from whatifs.core import scrub as _scrub          # the same scrubbing every log line gets
except Exception:
    _scrub = str

def _lines(text): return [ANSI.sub("", l).rstrip() for l in str(text).splitlines() if l.strip()]

def unit(text, rc, cap=MAX_ERRORS):
    """pytest -q log -> [(level, title, message)]: every FAILED / ERROR line and every skip named by the no-skip rule, then the totals line."""
    ls = _lines(text); out = []
    total = next((l for l in reversed(ls) if re.search(r"\b\d+ (passed|failed|errors?|skipped)\b", l)), "")
    if rc != 0:
        causes = [l for l in ls if l.startswith(("FAILED ", "ERROR "))] + [l.strip() for l in ls if l.strip().startswith("SKIPPED ")]
        if any(l.startswith("NO-SKIP RULE") for l in ls): causes.insert(0, next(l for l in ls if l.startswith("NO-SKIP RULE")))
        for l in causes[:cap]: out.append(("error", "Unit tests", l))
        if len(causes) > cap: out.append(("error", "Unit tests", f"... and {len(causes) - cap} more (the full list is in the job summary on the same page)"))
        if not causes: out.append(("error", "Unit tests", f"exit code {rc} with no FAILED line; the log ends: " + " | ".join(ls[-3:])))
    out.append(("notice" if rc == 0 else "error", "Unit tests", total.strip("= ") or f"no totals line (exit code {rc})"))
    return out

def rehearsal(text, rc):
    """Rehearsal log -> [(level, title, message)]: the episode id (the fake pipeline is seeded by it, so it reproduces the run), failed checks with their reason, the last error line."""
    ls = _lines(text); out = []
    ep = next((m.group(0) for l in ls for m in [re.search(r"EP\d{12}", l)] if m), "")
    green = rc == 0 and any("REHEARSAL: GREEN" in l for l in ls)
    gates = {}
    for l in ls:
        m = re.search(r"contract (script|final): \d+/\d+ pass", l)
        if m: gates.setdefault(m.group(1), m.group(0))                  # the first verdict of each gate = the rehearsal's own episode
    if green:
        out.append(("notice", "Rehearsal", f"REHEARSAL: GREEN, episode id {ep or 'unknown'}; " + "; ".join(gates.get(k, f"contract {k}: no line") for k in ("script", "final"))))
        return out
    reasons = [re.sub(r"^\[\w+\]\s*", "", l) for l in ls if re.search(r"contract (script|final) \w+: ", l)]          # one line per failed check, with its evidence
    for l in reasons[-(MAX_ERRORS - 3):]: out.append(("error", "Rehearsal", l))
    last = next((l for l in reversed(ls) if re.match(r"^(\w+\.)*\w*(Error|Exception|Breach)\b|^AssertionError|^KeyError", l)), "")
    out.append(("error", "Rehearsal", (last or "no error line; the log ends: " + " | ".join(ls[-2:]))))
    out.append(("error", "Rehearsal", f"RED (exit code {rc}), episode id {ep or 'unknown'}. Same run on any machine: python tools/sweep.py --mode rehearsal --ids {ep or '<episode id>'} --work <folder outside the repo>"))
    return out

def command(level, title, message):
    """One GitHub workflow command; the message is scrubbed, cut and escaped the way the runner expects."""
    m = _scrub(message)[:600].replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    t = str(title).replace("%", "%25").replace(",", "%2C").replace(":", "%3A")
    return f"::{level} title={t}::{m}"

def summary(kind, text, rc, path=None):
    """The same findings, uncapped, as a job summary (GitHub shows it under the annotations): written only where the runner names the file."""
    path = path or os.environ.get("GITHUB_STEP_SUMMARY", "")
    if not path: return False
    rows = unit(text, rc, cap=200) if kind == "unit" else rehearsal(text, rc)
    state = "GREEN" if all(level == "notice" for level, _, _ in rows) else "RED"
    lines = [f"### {rows[0][1]}: {state}"] + ["- `" + _scrub(m)[:600].replace("`", "'") + "`" for _, _, m in rows]
    with open(path, "a", encoding="utf-8") as f: f.write(chr(10).join(lines) + chr(10) * 2)
    return True

def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    if len(a) != 3 or a[0] not in ("unit", "rehearsal"): print("usage: python tools/ci_report.py unit|rehearsal <log file> <exit code>"); return 2
    try: text = open(a[1], encoding="utf-8", errors="replace").read()
    except OSError as e: text = f"log file missing: {e}"
    try: rc = int(a[2])
    except ValueError: rc = 1
    for level, title, msg in (unit if a[0] == "unit" else rehearsal)(text, rc): print(command(level, title, msg))
    summary(a[0], text, rc)
    return 0          # reporting never changes the result: the workflow step exits with the code of the tests

if __name__ == "__main__":
    sys.exit(main())
