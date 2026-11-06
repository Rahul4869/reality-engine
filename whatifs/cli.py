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

