> HISTORICAL - DO NOT FOLLOW. Superseded by CLAUDE.md (how to change the code) on 10 Nov 2026 (v12 truth hygiene). Kept unedited below as history.

# LAPTOP CHANGE PROMPT — paste into the Claude desktop app (Code tab) or a claude.ai chat, then describe your change

---

You are making ONE change to my automated YouTube channel's code (GitHub repo `reality-engine`), using my Claude subscription (no API money). I am not technical: babysit me, one step per message, and tell me exactly what to click. I sign in and press final buttons myself; never ask me for passwords or secret keys.

Before writing code:
1. Get the code: in the Claude Code tab, clone the repo; in a chat, ask me to upload GitHub → Code → Download ZIP.
2. Read `CLAUDE.md`, `docs/KERNEL.md` and `docs/DECISIONS.md` (if present). Obey them:
   - a Settings switch with a safe default for every new behaviour;
   - one-time migrations only for cells still at their old default;
   - no model names in code;
   - never weaken a quality gate;
   - never exceed the budget cap;
   - tests for the happy path and the failure paths;
   - a dated line in `docs/CHANGES.md`.
3. Discuss my idea honestly: value, risk, cost per month, and a better version if there is one. Wait for my "go".

Then:
4. Build it on a new branch named `laptop/<short-name>`.
5. Run `python tools/plan_guard.py`, the tests (`python -m pytest tests -q`; in a chat sandbox use `tools_sandbox/` if pytest is missing), and the rehearsal `WI_FAKE=1 WI_SMALL=1 WI_WORK=rh python -m whatifs.cli rehearsal`. Paste the numbers. Never call it done otherwise.
6. Get it to GitHub:
   - **Claude Code:** commit, push the branch, open a pull request with `gh pr create`.
   - **Chat:** give me the CHANGED files as a zip, then use Claude in Chrome to open the repo's "Add file → Upload files" page on a new branch. I drag the files in and click Commit; you open the pull request page and I click Create.
7. Wait for GitHub Checks. When green, tell me to tap Merge (or click it on the pull request page). If red, fix on the same branch.
8. End with one line for my project memory: what changed, the setting that switches it off, the cost.
