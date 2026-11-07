"""whatifs/preview.py v8.10 - Script Preview: scout + writers' room ONLY (no pictures, no voice, no upload), then ONE email with the title, the hook, the full
script, the shot list with POV notes and the estimated cost of the full video. Saved as a DRAFT in the Script_Previews tab WITHOUT using up the premise
(nor the next-episode tease) until it is approved. Approve / reject = one click from the email (a pre-filled GitHub issue 'APPROVE DRAFT...' /
'REJECT DRAFT...', owner-only, workflow preview.yml). With PREVIEW_USE_APPROVED the next production slot uses the approved draft (its writing is not paid
for twice; the voice, the real-timing shot list and the pictures are made then). Cost of a preview: the writing allowance only (about Rs 150-200)."""
from __future__ import annotations
import base64, html, json, re, zlib
from whatifs.core import S, store, log, iso, now_utc, env, JOB, flush_log, set_setting, scrub, safe_rows

def _pack(obj):
    return "z:" + base64.b64encode(zlib.compress(json.dumps(obj, ensure_ascii=False, default=str).encode(), 9)).decode()
def _unpack(s):
    s = str(s or "")
    if s.startswith("z:"): return json.loads(zlib.decompress(base64.b64decode(s[2:])).decode())
    return json.loads(s or "{}")

def _link(action, draft):
    from urllib.parse import quote
    repo = env("GH_REPO")
    if not repo: return ""
    return f"https://github.com/{repo}/issues/new?title={quote(action + ' ' + draft)}&body={quote('Press Submit new issue. The robot records your decision.')}"

def approx_units(script_text):
    """Narration units with ESTIMATED times (words / WPM + small gaps): enough for the Director to plan a preview shot list. Production re-times everything."""
    from whatifs.voice import parse_script
    wpm = S("WPM_ESTIMATE", float); t = 0.35; out = []
    for i, u in enumerate(parse_script(script_text)):
        d = max(0.6, len(u.text.split()) / wpm * 60); t += 0.35 + u.gap_before
        out.append({"i": i, "text": u.text, "tag": u.tag, "speaker": u.speaker, "start": round(t, 2), "end": round(t + d, 2), "curve": (u.curve or []) + (u.events or [])}); t += d
    return out

def estimate(d, plan):
    from whatifs.episode import est_cost_inr
    return round(est_cost_inr(d), 0)

def run():
    """python -m whatifs.cli preview  (workflow 'Script Preview'). Never publishes, never buys a picture."""
    JOB["name"] = "preview"
    from whatifs.sampler import draw as DRAW
    from whatifs import governor as G, room as ROOM, premise as PR, craft as CR
    from whatifs.episode import _apply_tier, _strip_beats, est_cost_inr
    from whatifs import publish as PUB
    draft = "DRAFT" + now_utc().strftime("%Y%m%d%H%M"); JOB["episode"] = draft
    d = DRAW(draft, "collective")
    plan = G.plan_for_episode(est_cost_inr(d), G.episodes_left_this_month())
    if plan.get("hold"): raise RuntimeError(plan["reason"] + " - no preview written (nothing spent)")
    d["kling"], d["living"] = plan["kling"], plan["living"]; _apply_tier(d, plan)
    if G.production_room_inr() < S("LLM_EST_INR", float) + S("THINK_EST_INR", float):
        raise RuntimeError("not enough budget left this month for a preview (nothing spent)")
    try: room = ROOM.run_room(d, draft)
    except (PR.SkipSlot, CR.BelowBar) as e:
        PUB.email("Script Preview: nothing reached the bar", f"<p>No draft was saved. {html.escape(str(e))}</p><p>Every pitch and score is in the Premise_Scores tab.</p>")
        log(f"preview: {e}", "WARN"); flush_log(); return {"ok": False, "why": str(e)[:300]}
    clean, _ = _strip_beats(room["script"]["script"]); units = approx_units(clean)
    import time as _t9; t_sp = _t9.time()
    try: shots = ROOM.plan_shots(room, units, d, plan, draft)
    except Exception as e: log(f"preview shot list failed: {scrub(e)[:160]}", "WARN"); shots = []
    room.setdefault("stage_times", d.get("stage_times") or {})["shot plan"] = round(_t9.time() - t_sp, 1)      # v9.2
    est = estimate(d, plan); spine = room["spine"]
    title = str((spine.get("promise") or {}).get("title") or spine.get("headline") or spine.get("premise"))
    hook = " ".join(u["text"] for u in units[:3])[:400]
    store().append("Script_Previews", [{"draft_id": draft, "created": iso(), "status": "DRAFT", "premise": spine.get("premise", "")[:200], "title": title[:120],
                                         "hook": hook, "est_cost_inr": est, "approved_at": "", "episode_id": "", "room_json": _pack({"d": d, "room": room}),
                                         "note": f"premise score {spine.get('premise_score', '')}; Owner's Cut {d.get('owners_cut', {}).get('mean', '')}"}])
    rows = "".join(f"<tr><td>{i}</td><td>{html.escape(s.get('type', ''))}</td><td>{html.escape(str((s.get('pov') or {}).get('vantage', '')))} "
                   f"{html.escape(str(s.get('pov_fx') or ''))}</td><td>{html.escape(str(units[i]['text'])[:90])}</td><td>{html.escape(str(s.get('prompt') or s.get('search') or '')[:180])}</td></tr>"
                   for i, s in enumerate(shots[:80]) if i < len(units))
    body = (f"<h2>{html.escape(title)}</h2><p><b>Premise:</b> {html.escape(spine.get('premise', ''))}<br><b>Hook:</b> {html.escape(hook)}<br>"
            f"<b>Estimated cost of the full video:</b> about Rs {est:.0f} (this preview cost only its writing). <b>Month left for production:</b> about Rs {G.production_room_inr():.0f}</p>"
            f"<p><a href='{_link('APPROVE', draft)}'>APPROVE (the next slot makes this video)</a> &nbsp; | &nbsp; <a href='{_link('REJECT', draft)}'>REJECT</a></p>"
            f"<h3>Script</h3><pre style='white-space:pre-wrap;font-family:sans-serif'>{html.escape(room['script']['script'])}</pre>"
            f"<h3>Shot list (POV notes)</h3><table border=1 cellpadding=3><tr><th>#</th><th>type</th><th>POV</th><th>line</th><th>prompt</th></tr>{rows}</table>")
    try:                                                          # v9: the full projected cost, and a flag when this preview's writing ran >10 % over
        from whatifs import costguard as CG
        cf = CG.preview_cost_flags(draft)
        body += ("<h3>Projected cost per line</h3><ul>" + "".join(f"<li>{k}: about Rs {v:.0f}</li>" for k, v in cf["lines"].items()) + "</ul>"
                 + (f"<p><b>Flag:</b> the writing cost Rs {cf['ai_measured']:.0f}, more than 10% over its estimate (Rs {cf['ai_estimate']:.0f}).</p>" if cf["flag"] else ""))
    except Exception as e: log(f"preview cost lines skipped: {scrub(e)[:120]}", "WARN")
    try:                                                          # v9.2: where the writing money and the time went (per role, per stage)
        from whatifs.core import flush_costs
        flush_costs(); per = {}
        for r_ in store().rows("Cost_Log"):
            if r_.get("episode_id") == draft and r_.get("basis") != "summary":
                k_ = r_.get("role") or r_.get("item") or "?"
                try: per[k_] = per.get(k_, 0.0) + float(r_.get("inr") or 0)
                except Exception: pass
        tt = (room.get("stage_times") if isinstance(room, dict) else None) or (d.get("stage_times") or {})
        body += ("<h3>Writing cost by role (this preview only; background jobs are not included)</h3><ul>" +
                 "".join(f"<li>{html.escape(k)}: Rs {v:.1f}</li>" for k, v in sorted(per.items(), key=lambda kv: -kv[1])) + f"</ul><p>Total Rs {sum(per.values()):.0f}</p>"
                 "<h3>Time by stage</h3><ul>" + "".join(f"<li>{html.escape(k)}: {v / 60:.1f} min</li>" for k, v in tt.items()) + f"</ul><p>Total {sum(tt.values()) / 60:.1f} min</p>")
    except Exception as e: log(f"preview breakdown skipped: {scrub(e)[:120]}", "WARN")
    PUB.email(f"Script Preview: {title[:60]}", body)
    log(f"preview {draft} saved as DRAFT (premise not used up)"); flush_log()
    return {"ok": True, "draft": draft, "est_cost_inr": est, "shots": len(shots)}

def decide(title):
    """'APPROVE DRAFT...' / 'REJECT DRAFT...' from the owner's one-click issue. v9: 'PICK EP<id> B' applies a packaging pick."""
    if re.match(r"^(APPROVE|REDO) SHEET ", str(title or "").strip()):
        from whatifs import sheets as SH
        return SH.decide(title)
    if str(title or "").strip().startswith("PICK "):
        from whatifs import packaging as PK
        return PK.apply_pick(title)
    m = re.match(r"^(APPROVE|REJECT) (DRAFT\d{8,14})$", str(title or "").strip())
    if not m: raise SystemExit("usage: python -m whatifs.cli previewdecide 'APPROVE DRAFT<id>'")
    act, draft = m.groups(); st = store()
    row = next((r for r in st.rows("Script_Previews") if r.get("draft_id") == draft), None)
    if not row or row.get("status") not in ("DRAFT", "APPROVED", "REJECTED"): raise RuntimeError(f"{draft} is not an open draft")
    st.update("Script_Previews", "draft_id", draft, {"status": "APPROVED" if act == "APPROVE" else "REJECTED", "approved_at": iso() if act == "APPROVE" else ""})
    log(f"preview {draft} {act.lower()}d by the owner"); flush_log(); return act

def take_approved(ep):
    """The oldest APPROVED draft for this production (marked USED with the episode id), or None. Returns (saved draw, room)."""
    if not S("PREVIEW_USE_APPROVED", bool): return None
    st = store()
    for r in st.rows("Script_Previews"):
        if r.get("status") != "APPROVED": continue
        try: data = _unpack(r.get("room_json"))
        except Exception as e:
            log(f"approved draft {r.get('draft_id')} unreadable ({scrub(e)[:80]}) - skipped", "WARN"); st.update("Script_Previews", "draft_id", r["draft_id"], {"status": "BROKEN"}); continue
        st.update("Script_Previews", "draft_id", r["draft_id"], {"status": "USED", "episode_id": ep})
        log(f"using the approved Script Preview {r['draft_id']} (its writing is not paid for again)", episode=ep)
        return data.get("d") or {}, data.get("room") or {}
    return None
