"""Generates docs/CURRENT/SYSTEM.md from the live code (run: python tools/gen_docs.py); the test suite fails when the committed file differs. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import ast, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path: sys.path.insert(0, ROOT)
OUT = os.path.join(ROOT, "docs", "CURRENT", "SYSTEM.md")

# The settings a build or setup chat must know (group -> keys). Value and note are read from core.DEFAULTS, never typed here.
KEY_SETTINGS = [
    ("Money", ["BUDGET_CEILING_INR", "BUDGET_FLOOR_INR", "MONTH_CAP_OVERRIDES", "BUDGET_GUARD_PCT", "BREAKOUT_FUND_CAP_INR", "BUDGET_MODE", "STANDARD_MAX_LONG_PER_MONTH"]),
    ("Schedule and formats", ["PUBLISH_DAYS", "SHORTS_TRACK_ON", "SHORTS_PER_DAY", "CASEFILES_ON", "DEEP_TRIAL_ON", "PREPROD_ON", "PAUSED"]),
    ("Writers' room and show", ["ROOM_MODE", "ROOM_V2_DRAFTS", "SHOW_MODE", "CONSTITUTION", "BRAIN_ON", "BRAIN_HOLDOUT"]),
    ("Pictures, motion, voice", ["ART_STYLE", "FAL_HERO_MODEL", "FAL_STILL_MODEL", "ANIM_SHOTS", "PARTICLES_ON", "LIVING_CHARACTERS_ON", "LIFE_LAYER_ON", "TTS_ENGINE"]),
    ("Quality gates", ["CONTRACT_ON", "CONTRACT_OFF", "BREAKOUT_HARD_BAR", "REHOOK_MAX_GAP_SEC", "JOKE_EVERY_SEC_LONG", "VISUAL_CHANGE_MAX_S", "PROMISE_BY_SEC", "IDEA_MIN_MULTIPLE"]),
    ("Owner", ["WA_ON", "BUILDS_ON", "DASH_ON"]),
    ("Knowledge Palace", ["PALACE_ON", "PALACE_PLAYBOOK_TOKENS", "PALACE_PLAYBOOK_TOKENS_BY_DEPT", "PALACE_LIMITS_SHARE", "PALACE_REVIEW_DAYS", "PALACE_KIND_CAPS"]),
]

# The v12 "Organisation" build, batch by batch. Edit ONLY when a batch is accepted (handoff_v12/BUILD_STATE.md is the detailed record).
ORG_STATUS = [
    ("Truth hygiene: one current truth (this file, the registry of retired concepts, check `docs_current`)", "built"),
    ("Knowledge Palace core (`whatifs/org/palace.py`: guarded items, life cycle, versions, bounded playbooks, founding knowledge, check `palace_health`; section 10)", "built"),
    ("Playbooks injected into every department's prompts and cited back (checks `palace_injected`, `palace_cited`), the Librarian's merges, outcome scores", "not built yet"),
    ("Memos and the department contract", "not built yet"),
    ("Execution Engine (every decision becomes a verified change in what runs)", "not built yet"),
    ("R&D and Review Board, creative departments and Council, QA repair loop, learning loop, Owner Office", "not built yet"),
]

# Tabs whose name invites a wrong reading.
TAB_NOTES = {"Technique_Library": "the outlier-video library (techniques seen in other channels' outliers); NOT the learning core",
             "Technique_Evidence": "the learning core's evidence table (whatifs/brain.py)",
             "Playbook": "the older research rulebook (whatifs/playbook.py); NOT a Palace playbook",
             "Palace_Items": "the Knowledge Palace index (whatifs/org/palace.py)",
             "Palace_Versions": "one row per Palace change: running version + hash of the whole Palace",
             "Palace_Playbooks": "each distinct department playbook the Palace built (id = hash of its text)"}

def clean(note):
    """A settings note without its version / rule-number labels (those are history; the doc states only what is true now)."""
    n = re.sub(r"^\s*v\d+(?:\.\d+)*[a-z]?(?:-\w+)?(?:\s*\([^)]*\))?:\s*", "", str(note or ""))
    n = re.sub(r"\s*\(K\d+\w?\)", "", n)
    return n.replace("|", "/").strip()

def _cell(s):
    return str(s).replace("|", "/").replace("\n", " ").strip()

def _modules():
    rows = []
    for d in ("whatifs", "tools"):
        for dp, dn, fn in os.walk(os.path.join(ROOT, d)):               # sub-packages too (whatifs/org)
            dn[:] = sorted(x for x in dn if x != "__pycache__")
            for f in sorted(fn):
                if not f.endswith(".py"): continue
                src = open(os.path.join(dp, f), encoding="utf-8").read()
                if not src.strip(): continue
                doc = (ast.get_docstring(ast.parse(src)) or "").strip().splitlines()
                rows.append((os.path.relpath(os.path.join(dp, f), ROOT).replace(os.sep, "/"), (doc[0] if doc else "").replace(" See docs/CURRENT/SYSTEM.md.", "")))
    return rows

def _palace(A):
    """Section 10: the Knowledge Palace, read from whatifs/org/palace.py and the seed files (never typed here)."""
    from whatifs.org import palace as PAL, DEPARTMENTS, STAGES
    items, bad = PAL.seed_items()
    by_kind, by_file = {}, {}
    for it in items:
        by_kind[it["kind"]] = by_kind.get(it["kind"], 0) + 1; by_file[it["seed_file"]] = by_file.get(it["seed_file"], 0) + 1
    A("## 10. Knowledge Palace (`whatifs/org/palace.py`)")
    A("- One repository every department reads and writes. Index: tab `Palace_Items` (one row per item; enough to build a playbook in one read). Full bodies:")
    A("  founding items resolve from `whatifs/org/seed/`, runtime items live in the Drive folder palace/. Nothing is ever deleted.")
    A(f"- Kinds ({len(PAL.KINDS)}): {', '.join(PAL.KINDS)}. Limits (served first, never dropped silently): {', '.join(PAL.LIMIT_KINDS)} and every item holding the owner's words.")
    A(f"- Statuses: {', '.join(PAL.STATUSES)}. Only {', '.join(PAL.SERVABLE)} can reach a prompt (`palace.servable`, the guard that runs before any ranking).")
    A("- The write gate (`palace.check`): dated evidence is required, trust is computed from the evidence type, every `applied_in` reference must exist in the code,")
    A("  and text that names a retired concept, reads like an instruction to a model or proposes gaming the platform is refused.")
    A("- Evidence types and the trust code gives them: " + ", ".join(f"{k} {v}" for k, v in PAL.EVIDENCE.items()) + ".")
    A("- The owner's words change only by the owner. An item that is retired or superseded sends everything derived from it back for re-validation (`palace._cascade`).")
    A("- Expiry: past `review_by` an item leaves every playbook until re-validated; a limit stays served, marked review due, and is reported.")
    A(f"- Playbook (`palace.playbook(dept, stage, topic)`): guard, then lanes (limits, proven, accepted, testing), then relevance, filled under a hard cap of "
      f"{PAL.core.DEFAULTS['PALACE_PLAYBOOK_TOKENS'][0]} estimated tokens; limits hold a reserved share of {PAL.core.DEFAULTS['PALACE_LIMITS_SHARE'][0]}. "
      "Same Palace state = byte-identical text; `playbook_id` is the hash of the text.")
    A("- Runs in production: `palace.daily` in the learning job, `palace.maintain` in Setup, contract check `palace_health` on every episode.")
    A("- Not yet wired (later batches): injecting playbooks into department prompts, citing items back, the Council, the Librarian's merges, outcome scores.")
    A("")
    A(f"**Founding knowledge** ({len(items)} items in `whatifs/org/seed/`; {len(bad)} invalid): " + ", ".join(f"{k} {v}" for k, v in sorted(by_file.items())) + ".")
    A("By kind: " + ", ".join(f"{k} {v}" for k, v in sorted(by_kind.items())) + ".")
    A("")
    A("**Life cycle** (`palace.MOVES`; a move that is not listed is illegal for everyone)")
    A("")
    A("| from | to | who may make the move |")
    A("|---|---|---|")
    for (frm, to), who in PAL.MOVES.items(): A(f"| {frm} | {to} | {'anyone' if who == PAL.ANY else ', '.join(who)} |")
    A("")
    A("**Review window and size cap by kind** (days before re-validation, 0 = never; most served items)")
    A("")
    A("| kind | review days | cap |")
    A("|---|---|---|")
    for k in PAL.KINDS: A(f"| {k} | {PAL.REVIEW_DAYS[k]} | {PAL.KIND_CAPS[k]} |")
    A("")
    A("**Departments** (`whatifs/org/__init__.py`; stage = the stage a playbook is built for when none is named). Stages: " + ", ".join(STAGES) + ".")
    A("")
    A("| id | department | default stage |")
    A("|---|---|---|")
    for d, (name, stage) in DEPARTMENTS.items(): A(f"| {d} | {name} | {stage} |")
    A("")

def _jobs():
    rows = []; wd = os.path.join(ROOT, ".github", "workflows")
    for f in sorted(os.listdir(wd)):
        if not f.endswith((".yml", ".yaml")): continue
        t = open(os.path.join(wd, f), encoding="utf-8").read()
        name = (re.search(r"^name:\s*(.+)$", t, re.M) or [None, f])[1].strip().strip("\"'")
        crons = re.findall(r"cron:\s*[\"']([^\"']+)[\"']", t)
        trig = [k for k in ("workflow_dispatch", "repository_dispatch", "push", "pull_request", "issues", "issue_comment", "workflow_run") if re.search(rf"^\s+{k}:", t, re.M)]
        cmds = sorted(set(re.findall(r"whatifs\.cli\s+([a-z_0-9]+)", t)))
        rows.append((f, name, ", ".join(crons) or "-", ", ".join(trig) or "-", ", ".join(cmds) or "-"))
    return rows

def render():
    """The full text of docs/CURRENT/SYSTEM.md. Deterministic: the same code always gives the same text (no dates, no environment)."""
    from whatifs import core, contract as CON
    from whatifs import truth as TRU
    D = core.DEFAULTS
    val = lambda k: str(D[k][0])
    script = [f for f in CON.FEATURES if f[1] == "script"]; final = [f for f in CON.FEATURES if f[1] == "final"]
    mods, jobs = _modules(), _jobs()
    L = []
    A = L.append
    A("# SYSTEM - what Reality Engine does now")
    A("")
    A("GENERATED from the code by `python tools/gen_docs.py`. Never edit by hand: change the code, run the generator, commit both.")
    A("`tests/test_docs_current.py` fails when this file differs from what the code says, or when any current doc names a retired concept.")
    A("")
    A("## 1. Facts (read from the code)")
    A(f"- Channel: \"Reality on Trial\" (brand Reality Engine). Concept: `docs/CURRENT/CONCEPT.md`. Owner requirements: `docs/CURRENT/OWNER_REQUIREMENTS_LEDGER.md`.")
    A(f"- Money: hard cap Rs {int(float(val('BUDGET_CEILING_INR'))):,} a month, everything included (`BUDGET_CEILING_INR`); extras pause at {val('BUDGET_GUARD_PCT')}% of the cap; "
      f"breakout fund carries over at most Rs {int(float(val('BREAKOUT_FUND_CAP_INR'))):,}. One month can be overridden in `MONTH_CAP_OVERRIDES`.")
    A(f"- Quality: {len(CON.FEATURES)} HARD contract checks ({len(script)} at the script stage, {len(final)} on the final video). A FAIL holds the episode and asks the owner "
      f"(Rewrite / Approve anyway). No upload below Breakout Score {val('BREAKOUT_HARD_BAR')}.")
    A(f"- Writers' room: mode `{val('ROOM_MODE')}` ({val('ROOM_V2_DRAFTS')} drafts, blind cross-family jury, one checklist revision, joke tournament). Room v1 is an optional fallback.")
    A(f"- Animated scenes: {val('ANIM_SHOTS')} per long video on `{val('FAL_HERO_MODEL')}`; stills on `{val('FAL_STILL_MODEL')}`; look `{val('ART_STYLE')}`; voice engine `{val('TTS_ENGINE')}`.")
    A(f"- Cadence: at most {val('STANDARD_MAX_LONG_PER_MONTH')} long videos a month, on {val('PUBLISH_DAYS')} (US Eastern); "
      f"{val('SHORTS_PER_DAY')} standalone Shorts a day; spin-offs: the Case Files countdown and the monthly Deep Trial.")
    A(f"- Size: {len(mods)} code modules, {len(D)} settings, {len(core.TABS)} Sheet tabs, {len(jobs)} GitHub workflows.")
    A("")
    A("## 2. How it runs")
    A("- Code: the Python package `whatifs/` runs on GitHub Actions (`python -m whatifs.cli <command>`). State lives in one Google Sheet (tabs and columns are")
    A("  append-only), media in Google Drive. A Cloudflare Worker (`mission_control/worker.js`) relays WhatsApp, serves the phone dashboard and is the watchdog clock.")
    A("- Providers: fal (clips and stills), Gemini (text, images, designed voices), Claude (showrunner, writer, jury member, chores), ffmpeg + OpenCV (render).")
    A("  Model names are never typed in code: they are discovered live (`whatifs/models.py`) or held in Settings cells.")
    A("- One long episode: tick (`whatifs/manage.py`) -> writers' room (`whatifs/room2.py`, early through `whatifs/preprod.py`) -> script-stage contract ->")
    A("  voice -> shot plan -> paid pictures and clips -> render (`whatifs/render.py`) -> final-stage contract -> held for the owner or scheduled ->")
    A("  release with Shorts and Reels -> 48-hour breakout monitor (`whatifs/breakout.py`) -> learning (`whatifs/brain.py`). Every paid step is checkpointed.")
    A("- Money: every paid call is logged (`core.cost`), estimated before it runs and stopped by the governor (`whatifs/governor.py`).")
    A("- Fake mode: `WI_FAKE=1` replaces every provider (`whatifs/fakes.py`); the rehearsal (`tools/rehearsal.py`) runs the whole pipeline at zero cost.")
    A("")
    A("## 3. The v12 Organisation build (status)")
    for what, st in ORG_STATUS: A(f"- {what}: **{st}**")
    A("")
    A("## 4. Truth rules (enforced by `whatifs/truth.py`)")
    A("- Follow only `docs/CURRENT/` and `CLAUDE.md`. `docs/ARCHIVE/` is history: never follow it.")
    A("- Version labels and rule numbers inside code comments are history labels, not instructions.")
    A(f"- Retired concepts ({len(TRU.RETIRED)} rules). Naming one in a current doc, a module docstring or a prompt fails Plan Guard, the tests and check `docs_current`:")
    for r in TRU.RETIRED: A(f"  - `{r['id']}`: {r['truth']}.")
    A("")
    A("## 5. Contract checks (`whatifs/contract.py` FEATURES)")
    A("| check | stage | what it guarantees |")
    A("|---|---|---|")
    for fid, stg, _probe, what in CON.FEATURES: A(f"| {fid} | {stg} | {_cell(what)} |")
    A("")
    A("## 6. Settings that matter (defaults from `core.DEFAULTS`; the live Sheet wins)")
    for group, keys in KEY_SETTINGS:
        A(f"**{group}**")
        A("")
        A("| setting | default | meaning |")
        A("|---|---|---|")
        for k in keys: A(f"| {k} | {_cell(D[k][0]) or '(blank)'} | {clean(D[k][1])} |")
        A("")
    A("## 7. Jobs (`.github/workflows/`)")
    A("| file | name | schedule (cron, UTC) | other triggers | cli commands |")
    A("|---|---|---|---|---|")
    for r in jobs: A("| " + " | ".join(_cell(x) for x in r) + " |")
    A("")
    A("## 8. Sheet tabs (`core.TABS`; append-only)")
    A("| tab | columns | first columns | note |")
    A("|---|---|---|---|")
    for name, cols in core.TABS.items(): A(f"| {name} | {len(cols)} | {_cell(', '.join(map(str, cols[:6])))}{' ...' if len(cols) > 6 else ''} | {TAB_NOTES.get(name, '')} |")
    A("")
    A("## 9. Modules")
    A("| module | purpose |")
    A("|---|---|")
    for rel, purpose in mods: A(f"| {rel} | {_cell(purpose)} |")
    A("")
    _palace(A)
    return "\n".join(L)

def drift():
    """'' when the committed SYSTEM.md equals the code; otherwise a one-line reason."""
    if not os.path.exists(OUT): return "docs/CURRENT/SYSTEM.md is missing: run python tools/gen_docs.py"
    have = open(OUT, encoding="utf-8").read().replace("\r\n", "\n"); want = render()
    if have == want: return ""
    a, b = have.splitlines(), want.splitlines()
    i = next((k for k in range(min(len(a), len(b))) if a[k] != b[k]), min(len(a), len(b)))
    return f"docs/CURRENT/SYSTEM.md differs from the code at line {i + 1} (run python tools/gen_docs.py): code says '{(b[i] if i < len(b) else '<end>')[:110]}'"

def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f: f.write(render())
    print("wrote docs/CURRENT/SYSTEM.md")
    return 0

if __name__ == "__main__":
    sys.exit(main())
