"""Department wrappers: what each wrapped production step reports about its own output (measures, lessons, problem memos) when it runs under the department runner. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import os
from whatifs.core import iso, store
from whatifs.org import memos as MEM, registry as REG

def _len(x):
    try: return len(x)
    except TypeError: return 0

# ------------------------------------------------------------------ measures: numbers read from the step's real output (never estimated, never typed)
def m_room(room):
    """D4 write: the script the room delivered."""
    room = room if isinstance(room, dict) else {}; sc = room.get("script"); bible = room.get("bible")
    script = str((sc.get("script") if isinstance(sc, dict) else "") or "")
    return {"script_words": len(script.split()), "beats": _len((bible.get("beats") if isinstance(bible, dict) else None) or []), "punch_marks": script.count("[PUNCH]"), "send_marks": script.count("[SEND]")}

def m_voice(vo):
    """D7 voice: the narration as recorded."""
    return {"narration_sec": round(float(getattr(vo, "duration", 0) or 0), 1)}

def m_pkg(pkg):
    """D5 package: titles, tags and the thumbnail brief."""
    pkg = pkg if isinstance(pkg, dict) else {}
    return {"titles": _len(pkg.get("titles") or []), "tags": _len(pkg.get("tags") or []), "thumb_prompt_chars": len(str(pkg.get("thumb_prompt") or ""))}

def m_shots(shots):
    """D6 plan: the shot plan by kind."""
    shots = [s for s in shots if isinstance(s, dict)] if isinstance(shots, (list, tuple)) else []
    return {"shots": len(shots), "animated_shots": sum(1 for s in shots if s.get("type") in ("kling", "living")), "still_shots": sum(1 for s in shots if s.get("type") == "still")}

def m_assets(files):
    """D6 assets: what was really delivered."""
    files = files if isinstance(files, dict) else {}; dl = files.get("delivered") or {}
    return {"images": _len(files.get("img") or {}), "clips": _len(files.get("clips") or {}), "anchors": _len(files.get("anchors") or []),
            "kling_delivered": int(dl.get("kling") or 0) if isinstance(dl, dict) else 0}

def m_render(master):
    """D6 render: the finished master file."""
    try: mb = round(os.path.getsize(master) / 1e6, 2)
    except (OSError, TypeError): mb = 0
    return {"master_mb": mb, "master_made": 1 if mb > 0 else 0}

def m_upload(vid):
    """D9 publish: did the platform return a video id."""
    return {"uploaded": 1 if vid else 0}

def m_gate(g):
    """D8 gates: how many promises were checked and how many held."""
    g = g if isinstance(g, dict) else {}; rows = g.get("rows") or []
    return {"checks": len(rows), "passed": sum(1 for r in rows if r.get("status") == "PASS"), "failed": _len(g.get("failed") or []),
            "waived": sum(1 for r in rows if r.get("status") == "WAIVED")}

def m_learn(_result=None):
    """D10 daily: the size of what the learning job keeps."""
    st = store()
    def n(tab):
        try: return len(st.rows(tab))
        except Exception: return 0
    return {"analytics_rows": n("Analytics"), "evidence_rows": n("Technique_Evidence"), "palace_items": n("Palace_Items")}

# ------------------------------------------------------------------ D8: a failed promise becomes a problem memo for the department that owns it
def gate_lessons(g):
    return [(f"check:{fid}", f"check {fid} failed: {str(ev)[:220]}") for fid, ev in ((g or {}).get("failed") or [])]

def gate_memos(ep, stage):
    """emit hook for a gate run: one problem memo per failed check, addressed to the owning department. When the contract held the episode the
    owner already has the contract's own message, so the watchdog must not send a second one about the same failure."""
    def emit(g, brief):
        out = []; held = not (g or {}).get("ok", True)
        for fid, ev in ((g or {}).get("failed") or []):
            m = {"type": "problem_memo", "from_dept": "D8", "to_depts": [REG.check_owner(fid)], "subject": f"{fid} failed at the {stage} gate for {ep}"[:140],
                 "body": {"what_failed": f"contract check {fid}: {str(ev)[:300]}", "where": f"{ep} {stage} gate", "attempt": 1, "check": fid, "stage": stage},
                 "done_when": f"check {fid} passes for {ep}, or the owner waives it", "episode_id": ep, "dedupe_key": f"gate|{ep}|{stage}|{fid}",
                 "evidence": [{"source": f"Feature_Ledger:{ep}:{stage}:{fid}", "date": iso()[:10], "type": "own data", "finding": str(ev)[:300]}]}
            if held: m["_owner_told"] = "the contract's own hold message"
            out.append(m)
        return out
    return emit

def gate_settle(ep, stage):
    """settle hook for a gate run: an open problem memo of this episode and gate is closed by the ledger row of THIS run (passed = repair verified,
    waived = the owner's decision). Proof first: nothing is closed that this run did not check."""
    def settle(g, brief):
        rows = {r.get("feature"): r.get("status") for r in ((g or {}).get("rows") or [])}; out = []
        for m in MEM.find(type="problem_memo", from_dept="D8", episode_id=ep, stage=stage):
            s = rows.get(m["body"].get("check"))
            if s == "PASS": out.append((m["id"], "repair_verified", f"Feature_Ledger:{ep}:{stage}:{m['body'].get('check')}:PASS"))
            elif s == "WAIVED": out.append((m["id"], "owner_waived", f"Feature_Ledger:{ep}:{stage}:{m['body'].get('check')}:WAIVED"))
        return out
    return settle
