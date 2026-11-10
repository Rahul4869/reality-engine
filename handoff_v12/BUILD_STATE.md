# BUILD_STATE - Reality Engine v12 "Organisation"
Updated: 10 Nov 2026 (end of B0). Branch: `v12-organisation` (never main). Resume: read this file + `git log -5`.

## NEXT
**B1 - Truth hygiene** (01 section 11; 03 "B1"). Full seven-step MANDATORY BATCH LOOP. Effort: High.

## DONE
### B0 - Bootstrap & verify (10 Nov 2026) - ACCEPTED
- Laptop (Windows 11): installed Git 2.56, Python 3.12.10, ffmpeg/ffprobe 9.0.2 via winget. venv at `REALITY_ENGINE_HANDOFF/.venv` with the
  requirements.txt pins (numpy 2.0.2, opencv-headless 4.14, pillow 12.3, requests, pyyaml) + tzdata, soundfile, cryptography (Checks installs these too).
  Not installed: kokoro, transformers (no test needed them).
- Repo cloned, branch `v12-organisation` from main, commit "v11.1 baseline (from handoff)" pushed.
- Files only on main (kept, untouched): `.keepalive`, `PRIVACY.md`, `README.md`. 35 files only in the snapshot (v10.2-v11.1 work) are now on the branch.
- Plan Guard: GREEN.
- Full suite (59 files): **912 passed / 0 failed / 6 skipped** - see "How the number was reached" below (honest detail).
- Fake rehearsal (WI_FAKE=1 WI_SMALL=1): **GREEN** (contract script 19/19, final 18/18).

### How the number was reached (nothing hidden)
1. First full run on Windows: 897 / 15 failed. Causes, all traced:
   - 9 failures: `whatifs/reels.py` put a `C:\...` path into ffmpeg's `ass=` filter (drive colon + backslashes are filter syntax) -> every Short failed
     -> contract `shorts` FAIL. Windows-only. Fix: 2 lines guarded by `os.name == "nt"` (Linux/production path byte-identical).
   - 5 failures: `cryptography` missing in the venv (environment; installed).
   - 2 failures (`test_v86` brand position, `promise_paid` in the pipeline): no DejaVu font on Windows -> PIL's tiny fallback font. Environment fix,
     no code change: DejaVu TTFs copied to `C:\usr\share\fonts\truetype\dejavu\` (the Linux path the code already looks for).
2. Second full run: 911 / 1 failed: `test_v11_feel` particle test, intermittent (2 fails in 5 runs). ROOT CAUSE = REAL v11.1 BUG, not Windows:
   `render.Particles` seeded its RNG with Python's built-in `hash()` of a string, which is randomised per process -> particle layout differed every
   run, and some layouts of the "office" (rain) world scored 0.0-0.71 aliveness (< 0.75 bar). Fix: md5-based seed (same pattern as render.py:395).
   Re-ran test_v11_feel, test_v111_living, test_v9_render, test_v91_atmos, test_v11_breakout, test_integration, test_v91_e2e: all green; rehearsal GREEN.
   NOTE: the 912/0 total = second full run (911/1) + the fixed file re-run green. A single uninterrupted 912/0 full run after the last edit was not
   repeated (35 min); the next batch's full suite will confirm it.
- The pending `test_v91_flaky_root` re-run from the old handoff: 3/3 passed.

## CODE CHANGES IN B0 (2 files, both protected-area: say so in the final PR)
- `whatifs/reels.py`: Windows-only escaping of the subtitle/fonts path for ffmpeg (no effect on Linux).
- `whatifs/render.py`: deterministic particle seed (md5 instead of process-randomised hash()).

## OPEN ISSUES
1. (D6/D8, for B6-B7) Rain particles ("office" world) can read as a still for some seeds (aliveness 0.0 seen). Now deterministic, and seed 7 passes,
   but the particle layer has no guarantee per seed. Proper fix: after rendering, measure aliveness and re-seed/boost when below the bar (needs an
   enforcement check + failing test). Not done in B0 (no new features).
2. (B1) Repo `CLAUDE.md`, `docs/KERNEL.md`, `docs/CHANGES.md` still carry retired concepts (05_STALE_SCAN) - B1's job.
3. (laptop) Test temp dirs `mt_*` accumulate in `%TEMP%`; automatic cleanup of that shared folder was blocked by the app's safety rule. Disk free
   333 GB, so no risk; delete by hand only if space ever gets tight.

## HOW TO RUN ON THIS LAPTOP (PowerShell, from `reality-engine/`)
- First line of every shell: `$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')`
- Env: `$env:PYTHONUTF8='1'; $env:WI_FAKE='1'; $env:PY='../.venv/Scripts/python.exe'`
- Suite: `& "C:\Program Files\Git\bin\bash.exe" ../shim/runall.sh . <outdir outside repo>` (~35 min). Some files: `../shim/runseq.sh . <outdir> test_a test_b`.
- Rehearsal: `$env:WI_SMALL='1'; $env:WI_WORK='<dir outside repo>'; ..\.venv\Scripts\python.exe -m whatifs.cli rehearsal` (~3 min); delete the work dir after.
- Plan Guard: `..\.venv\Scripts\python.exe tools\plan_guard.py`.
- git: `core.autocrlf=false` set in this clone (keep LF); commit identity Rahul4869 (noreply address); push needs
  `$env:GIT_TERMINAL_PROMPT='1'; $env:GCM_INTERACTIVE='always'` (credentials are now saved).

## BATCH LOG
| Batch | Status | Suite | Rehearsal | Notes |
|---|---|---|---|---|
| B0 | done 10 Nov 2026 | 912 / 0 / 6 skipped | GREEN | 2 small fixes (Windows ffmpeg path; particle seed determinism) |
| B1 | next | | | Truth hygiene |
