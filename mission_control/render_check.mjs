import { readFileSync } from "node:fs";
const dump = process.argv.includes("--dump");                                                                // v12 B-OWNER: each tab's HTML as JSON on stdout (tests/test_v12_owner_face.py)
const args = process.argv.slice(2).filter(a => a !== "--dump");
const html = readFileSync(args[0] || new URL("./mission_control.html", import.meta.url), "utf8");      // v10.1: defaults for a bare run
const js = [...html.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/g)].map(m => m[1]).join("\n");
if (!args[1]) { console.log("usage: node render_check.mjs [mission_control.html] <snapshot.json> [--dump]   (the Dashboard check passes a real snapshot)"); process.exit(2); }
const snap = JSON.parse(readFileSync(args[1], "utf8"));
const el = () => ({ innerHTML: "", textContent: "", style: {}, dataset: {}, classList: { add(){}, remove(){}, toggle(){} }, setAttribute(){}, addEventListener(){}, appendChild(){}, focus(){}, querySelector: () => el(), querySelectorAll: () => [] });
const els = {};                                                                                             // one element a selector, so the view's HTML can be read back
globalThis.document = { querySelector: s => (els[s] ||= el()), querySelectorAll: () => [], addEventListener(){}, getElementById: () => el(), createElement: () => el(), body: el(), documentElement: el(), visibilityState: "visible" };
globalThis.window = { addEventListener(){}, scrollTo(){}, matchMedia: () => ({ matches: false, addEventListener(){} }), open(){} };
globalThis.location = { protocol: "https:", hash: "" }; globalThis.localStorage = { getItem: () => null, setItem(){} }; Object.defineProperty(globalThis, "navigator", { value: { vibrate(){} }, configurable: true });
globalThis.fetch = async () => ({ status: 200, ok: true, json: async () => snap });
globalThis.errors = []; globalThis.dumped = {};
const harness = js.replace(/\bload\(\);?\s*$/m, "") + `
;(async () => {
  try { S = await API.snapshot(); } catch (e) { errors.push("snapshot: " + e.message); }
  for (const t of ["home", "learning", "plan", "money", "inputs", "controls"]) {
    try { tab = t; render(); dumped[t] = document.querySelector("#view").innerHTML; } catch (e) { errors.push(t + ": " + e.message); }
  }
  console.log(errors.length ? "RENDER ERRORS:\\n" + errors.join("\\n") : "ALL TABS RENDERED");
  if (${dump}) console.log(JSON.stringify(dumped));
  process.exit(0);
})();`;
globalThis.process = process; try { new Function(harness)(); } catch (e) { console.log("SCRIPT ERROR: " + e.message); }
