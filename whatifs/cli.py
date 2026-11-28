"""Entry point for every GitHub workflow: python -m whatifs.cli <command>. See docs/CURRENT/SYSTEM.md."""
import sys, os, json, traceback
from whatifs.core import FAKE, JOB, log, flush_log

def _on_stop(signum, frame):
    """v8.3: GitHub cancels a job with SIGTERM / SIGINT. Write the spend and the log first, so a cancelled or timed-out job never loses its Cost_Log rows."""
    try:
        from whatifs.core import flush_costs
        flush_costs(); flush_log()
    finally:
        os._exit(143)

def research_round():
    """v12 B5: the first part of the daily learning job - R&D's daily run (the free collectors and the research agenda), its weekly deep research when
    due (paid, inside the R&D cap; an owner question makes it P0), then the Review Board whenever a research memo waits. A failure here is recorded
    by the department runner and never stops the learning job."""
    from whatifs.org import runner as ORG, rnd as RND, board as BRD
    try: ORG.work("D2", "daily", "", RND.daily)
    except Exception as x: log(f"R&D daily run failed: {type(x).__name__}: {str(x)[:160]}", "WARN")
    try:
        if RND.deep_due(): ORG.run("D2", "weekly", RND.deep, budget="org", urgency="P0" if RND.p0_waiting() else "P1")
    except ORG.CapReached as x: log(f"R&D weekly research waits: {x}", "WARN")
    except Exception as x: log(f"R&D weekly research failed: {type(x).__name__}: {str(x)[:160]}", "WARN")
    try:
        if BRD.due(): ORG.run("D3", "assess", BRD.assess, budget="org")
    except ORG.CapReached as x: log(f"Review Board waits: {x}", "WARN")
    except Exception as x: log(f"Review Board session failed: {type(x).__name__}: {str(x)[:160]}", "WARN")

def strategy_round():
    """v12 V4: the CEO's round inside the daily learning job, right after Growth & Learning's run: Finance's watch (D11). It returns at once unless the
    CEO is on (STRATEGY_ON), the Execution Engine is on (with the organisation or the engine off a decision could never become a ticket) and the
    channel is not paused (no decision for a channel that makes nothing; the first round after counts what arrived). Each run in its own try: a
    failure is recorded by the department runner and logged, never raised."""
    from whatifs.core import S
    from whatifs.org import runner as ORG, execute as EX, finance as FIN, strategy as STR
    from whatifs.manage import paused
    if not S("STRATEGY_ON", bool) or not EX.on() or paused(): return False
    try: ORG.run("D11", "watch", FIN.watch)
    except Exception as x: log(f"Finance watch failed: {type(x).__name__}: {str(x)[:160]}", "WARN")
    try: ORG.run("D1", "review", STR.review, settle=STR.stamp_resent)      # U1 fix 210: "resent" is stamped only after the runner wrote the ticket
    except Exception as x: log(f"Strategy review failed: {type(x).__name__}: {str(x)[:160]}", "WARN")
    try: STR.tell()                                                                         # level-triggered: a decision whose ticket is on tab Memos is told once
    except Exception as x: log(f"Strategy's message was not sent: {type(x).__name__}: {str(x)[:160]}", "WARN")
    return True

def strategy_catch_up():
    """v12 V4: the script gate judges strategy_live, but only the daily learning job runs the round - a production job that would meet a stale review
    (or a decision standing as text) runs the round first. Never stops the production."""
    try:
        from whatifs.org import strategy as STR
        if STR.live_issues()[0]:
            log("Strategy's round is overdue: this production job runs it first", "WARN"); strategy_round()
    except Exception as x: log(f"Strategy catch-up skipped: {type(x).__name__}: {str(x)[:160]}", "WARN")

def research_catch_up():
    """v12 B5: the script gate judges research_cadence, but only the daily learning job ran the round - a dropped cron, or an organisation switched
    back on after days, would HOLD a video for work any job can do. A production job that would meet a stale round runs it first (level-triggered:
    nothing happens while the learning job keeps its schedule). Never stops the production."""
    try:
        from whatifs.org import rnd as RND
        if RND.round_overdue():
            log("R&D's round is overdue (the daily learning job missed it): this production job runs it first", "WARN"); research_round()
    except Exception as x: log(f"R&D catch-up skipped: {type(x).__name__}: {str(x)[:160]}", "WARN")

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
            research_catch_up()                                         # v12 B5: never hold a video for a research round this job can run itself
            strategy_catch_up()                                         # v12 V4: nor for Strategy's round
            slot = sys.argv[2]; res = produce(slot)
            print(json.dumps({k: res.get(k) for k in ("ok", "episode", "yt")}, default=str))      # no title or file names in the public log
        elif cmd == "release1":                                         # the long video's release step (v12 V2c-b2b: one step - no cut-down reels follow)
            from whatifs.manage import release; release(sys.argv[2], cmd)
        elif cmd == "trends":
            from whatifs.manage import trend_scout; trend_scout()
        elif cmd == "learn":
            from whatifs.manage import learn, money_check
            from whatifs.org import runner as ORG, wraps as WR          # v12: the daily learning job is the Growth & Learning department's run
            research_round()                                            # v12 B5: R&D and the Review Board run first
            ORG.work("D10", "daily", "", lambda b: learn(), measure=WR.m_learn); strategy_round(); ORG.daily_check(); money_check()      # v12 V4: then the CEO's round
        elif cmd == "brief":
            from whatifs.manage import monthly_brief; monthly_brief()
        elif cmd == "research":
            from whatifs.research import main as rs; rs()
        elif cmd == "cutmap":
            if len(sys.argv) < 3: raise SystemExit("usage: python -m whatifs.cli cutmap <episode folder>")
            from whatifs.cutmap import main as cm; cm(sys.argv[2])
        elif cmd == "floorkit":                                          # v12 V1c (the judged floor): the video the owner rejected becomes the canary's kit, once
            from whatifs.org import floor as FLR
            from whatifs import notify as NT
            from whatifs.core import WORK
            if len(sys.argv) > 2: src, yt = sys.argv[2], (sys.argv[3] if len(sys.argv) > 3 else "")      # the tests and an offline run: a local file
            else:                                                      # the workflow "Floor kit": the link and the id are read from its event file - never printed or logged
                ev = json.load(open(os.environ["GITHUB_EVENT_PATH"]))["inputs"]; src = ev.get("link") or ""; yt = ev.get("yt") or ""
            if src:
                os.makedirs(WORK, exist_ok=True)
                sha = FLR.make_kit(FLR.fetch(src, os.path.join(WORK, "kit_src.mp4")), yt=yt)
                NT.send("floor_kit", f"The first-time-viewer check has its reference: the first minute of the video you gave is filed ({sha[:8]}). You can stop sharing the file now.",
                        tier="now", expires_h=72, dedupe_key=f"floorkit|{sha[:8]}")
            if len(sys.argv) <= 2 or (len(sys.argv) > 4 and sys.argv[4] == "pilot"):      # audit F11: the workflow run (and a test that asks for it) measures the judges on the kit
                p = FLR.pilot()
                held = FLR.fail_holds()                                   # code review C18 (2): the hold cell read AFTER the pilot - the notice says what the code will do
                if p.get("measured"):
                    said = f"were measured on the reference alone: they named the real minute over its frozen picture in {round(p['q'] * p['answers'])} of {p['answers']} answers."
                    then = ("From now a video they refuse is held for your tap." if held else "That is not enough to hold a video on their word: a video they refuse comes to you first and is published after your silence.")
                else:                                                     # its cap reached, a family down, too few answers: nothing was measured and nothing changes
                    said = "could not be measured on the reference alone (" + (f"only {p['answers']} answers came back" if p["answers"] else "they could not be asked") + "). Nothing changes."
                    then = ("A video they refuse is still held for your tap." if held else "A video they refuse still comes to you first and is published after your silence.")
                from whatifs.core import S as _S
                paid = f"This month's pilots have cost Rs {FLR.pilot_inr():.0f} of Rs {_S('VIEW_FLOOR_PILOT_CAP_INR', float):.0f}."      # code review C18 (8), RULINGS_U1c 4.3: the rupees, in both wordings
                NT.send("floor_kit", f"The first-time viewers {said} {then} {paid} Nothing is needed from you.", tier="now", expires_h=72, dedupe_key=f"floorpilot|{p['month']}|{p['answers']}|{p['q']}|{held}")
        elif cmd == "look_kit":                                         # v12 DRAWN-b L1b: his reference sheets become the look bar's kit (cell LOOK_REFS), once; no message
            from whatifs.org import look as LOOK
            parts = [a.rsplit("|", 2) for a in sys.argv[2:]]
            if not parts or any(len(x) != 3 for x in parts): raise SystemExit('usage: python -m whatifs.cli look_kit "<path>|<name>|<key,key,...>" ...')
            LOOK.make_kit([(p, n, ks.split(",")) for p, n, ks in parts])
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
            from whatifs.core import S as _S
            if str(_S("STYLE_SAMPLES_REQUEST") or "").upper() == "TRUE":      # v10.2: the first run shows the cast in 3 looks; the owner taps one
                from whatifs.sheets import style_samples as ss; print(json.dumps(ss(), default=str))
            else:
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
            if kind == "casefiles":                                      # v11 (K160): the monthly Case Files countdown
                from whatifs import spinoff as SPO
                print(json.dumps({k: v for k, v in SPO.run(force="--force" in sys.argv).items() if k != "path"}, default=str)); return
            if kind == "short":                                          # v11 (K159): one standalone Short (only when due unless --force)
                from whatifs import shorts2 as SH2
                print(json.dumps({k: v for k, v in SH2.run(force="--force" in sys.argv).items() if k != "path"}, default=str)); return
            if "--if-due" in sys.argv and not SP.due(): print("not due")
            else: print(SP.run(kind=kind, force=kind == "cast_intro"))
        elif cmd == "wa_inbound":                                        # v9.4b: WhatsApp messages / button taps / delivery statuses (encrypted)
            import os as _os
            from whatifs.wa import handle_inbound; from whatifs.dash import drain; drain(); print(handle_inbound(_os.environ.get("WA_PAYLOAD", "{}")))   # CH-1: the kept ones first, oldest first
        elif cmd == "wa_templates":                                      # v10.2 (#10/#11): subscribe the app, create the template; a failure fails the job (red, not green)
            from whatifs.wa import ensure_templates, ensure_subscribed
            sub = ensure_subscribed(); tpl = ensure_templates(); print({"subscribed": sub, "template": tpl})
            if not (sub and tpl) and not FAKE: sys.exit(1)
        elif cmd == "dash_action":                                       # v9.4b: one encrypted dashboard tap (from repository_dispatch)
            import os as _os
            from whatifs.dash import handle_action, drain; drain(); print("ok" if handle_action(_os.environ.get("DASH_PAYLOAD", "{}")) else "not done")   # CH-1: his own payload is kept too - the drain does it in its order, the call finds its ack
        elif cmd == "dash_drain":                                        # CH-4 (OE2-2): the tick's owner_inbox job - his kept inputs, oldest first, and nothing else
            from whatifs.dash import drain; print(drain())
        elif cmd == "dash_snapshot":
            import json as _json
            from whatifs.dash import build_snapshot; print(_json.dumps(build_snapshot())[:2000])
        elif cmd == "build_ready":                                       # v9.4a (WP3): claude-build.yml -> one owner message (Merge / Reject)
            from whatifs.builds import build_ready; print(build_ready(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else "", sys.argv[5] if len(sys.argv) > 5 else ""))
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

