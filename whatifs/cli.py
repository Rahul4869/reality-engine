"""whatifs/cli.py v8.10 - entry point for every GitHub workflow.  python -m whatifs.cli <command>"""
import sys, os, json, traceback
from whatifs.core import JOB, log, flush_log

def _on_stop(signum, frame):
    """v8.3: GitHub cancels a job with SIGTERM / SIGINT. Write the spend and the log first, so a cancelled or timed-out job never loses its Cost_Log rows."""
    try:
        from whatifs.core import flush_costs
        flush_costs(); flush_log()
    finally:
        os._exit(143)

def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "tick"
    JOB["name"] = cmd
    try:
        import signal; signal.signal(signal.SIGTERM, _on_stop); signal.signal(signal.SIGINT, _on_stop)
    except Exception: pass
    try:                                                       # v10.1b: PAUSED also stops the paid side jobs that run on their own schedule
        from whatifs.manage import paused as _paused           # (hand-started ones still run: cast intro, Script Preview, sheets, upload check)
        if _paused() and (cmd in ("preprod", "pilot") or (cmd == "special" and "--if-due" in sys.argv)):
            print("paused - nothing to do"); return
    except Exception: pass
    try:
        if cmd == "setup":
            from whatifs.manage import setup; setup()
        elif cmd == "voices":
            from whatifs.voice_lab import main as vl; vl()
        elif cmd == "tick":
            from whatifs.manage import tick
            a = tick(); print("ACTION", json.dumps(a))
            open(os.environ.get("GITHUB_OUTPUT", "/dev/null"), "a").write(f"action={a['action']}\nslot={a.get('slot','')}\nepisode={a.get('episode','')}\n")
        elif cmd == "produce":
            from whatifs.episode import produce
            slot = sys.argv[2]; res = produce(slot)
            print(json.dumps({k: res.get(k) for k in ("ok", "episode", "yt")}, default=str))      # no title or file names in the public log
        elif cmd in ("release1", "release2", "release3", "release4"):      # v8.5: reels 3-4 go out on the next days
            from whatifs.manage import release; release(sys.argv[2], cmd)
        elif cmd == "trends":
            from whatifs.manage import trend_scout; trend_scout()
        elif cmd == "learn":
            from whatifs.manage import learn, money_check; learn(); money_check()
        elif cmd == "brief":
            from whatifs.manage import monthly_brief; monthly_brief()
        elif cmd == "research":
            from whatifs.research import main as rs; rs()
        elif cmd == "cutmap":
            if len(sys.argv) < 3: raise SystemExit("usage: python -m whatifs.cli cutmap <episode folder>")
            from whatifs.cutmap import main as cm; cm(sys.argv[2])
        elif cmd == "abtest":
            from whatifs.tableread import abtest_main; abtest_main()
        elif cmd == "fixheld":
            from whatifs.episode import fix_held
            import re
            m = re.match(r"^FIX (EP\w+)$", (sys.argv[2] if len(sys.argv) > 2 else "").strip())
            if not m: raise SystemExit("usage: python -m whatifs.cli fixheld 'FIX <episode id>'")
            res = fix_held(m.group(1)); print(json.dumps({k: res.get(k) for k in ("ok", "held", "episode", "yt", "problems")}, default=str))
        elif cmd == "prready":                                            # v8.9: change-ready email with a one-click merge link
            from whatifs.manage import pr_ready; pr_ready()
        elif cmd == "preview":                                            # v8.10: Script Preview (scout + writers' room only, emailed as a DRAFT)
            from whatifs.preview import run as pv; print(json.dumps(pv(), default=str)[:300])
        elif cmd == "sheets":                                             # v9: the one-time character sheets (manual workflow only, lifetime image cap)
            from whatifs.sheets import run as sh; print(json.dumps(sh(), default=str))
        elif cmd == "previewdecide":
            from whatifs.preview import decide; print(decide(sys.argv[2] if len(sys.argv) > 2 else ""))
        elif cmd == "voicecheck":                                         # v8.10: which Gemini voices this key can use
            from whatifs.tts_gemini import voice_check; print(voice_check())
        elif cmd == "models":
            from whatifs.models import discover_models; print(discover_models())
        elif cmd == "rehearsal":
            from tools.rehearsal import run; run()
        elif cmd == "pilot":                                             # v10: a pilot Short (--if-due = only on PILOT_DAYS)
            from whatifs import pilots as PIL
            print("not due" if ("--if-due" in sys.argv and not PIL.due()) else PIL.run())
        elif cmd == "bakeoff":                                           # v10: the one-time model bake-off
            from whatifs import bakeoff as BKO; print(BKO.run(force="--force" in sys.argv))
        elif cmd == "special":                                           # v10: a special reel (--kind cast_intro|special; --if-due = only on SPECIALS_DAYS)
            from whatifs import specials as SP
            kind = sys.argv[sys.argv.index("--kind") + 1] if "--kind" in sys.argv else "special"
            if "--if-due" in sys.argv and not SP.due(): print("not due")
            else: print(SP.run(kind=kind, force=kind == "cast_intro"))
        elif cmd == "wa_inbound":                                        # v9.4b: WhatsApp messages / button taps / delivery statuses (encrypted)
            import os as _os
            from whatifs.wa import handle_inbound; print(handle_inbound(_os.environ.get("WA_PAYLOAD", "{}")))
        elif cmd == "wa_templates":
            from whatifs.wa import ensure_templates; print(ensure_templates())
        elif cmd == "dash_action":                                       # v9.4b: one encrypted dashboard tap (from repository_dispatch)
            import os as _os
            from whatifs.dash import handle_action; print("ok" if handle_action(_os.environ.get("DASH_PAYLOAD", "{}")) else "not done")
        elif cmd == "dash_snapshot":
            import json as _json
            from whatifs.dash import build_snapshot; print(_json.dumps(build_snapshot())[:2000])
        elif cmd == "build_ready":                                       # v9.4a (WP3): claude-build.yml -> one owner message (Merge / Reject)
            from whatifs.builds import build_ready; print(build_ready(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else ""))
        elif cmd == "preprod":                                           # v9.4a (WP2): the writers' room early, at half price
            from whatifs.preprod import run as _pp
            r = _pp(force="--force" in sys.argv, check_only="--check" in sys.argv); print(r)
        elif cmd == "nativetest":                                        # v9.3.1 (L5): the owner runs YouTube's own Test & Compare; the rescue stands aside
            from whatifs.packaging import native_test; print(native_test(sys.argv[2]))
        elif cmd == "upload_check":                                      # v9.3.1 (L1): the ₹0 upload check (replaces the API audit)
            from whatifs.launch import upload_check; print(upload_check(force="--force" in sys.argv))
        else:
            raise SystemExit(f"unknown command {cmd}")
    except Exception as e:
        log(f"{cmd} crashed: {e}\n{traceback.format_exc()[-2500:]}", "ERROR")
        from whatifs.core import scrub
        open("last_error.txt", "w").write(scrub(traceback.format_exc()))
        flush_log(); raise
    try:
        from whatifs.core import flush_costs; flush_costs()
    except Exception: pass
    flush_log()

if __name__ == "__main__":
    main()

