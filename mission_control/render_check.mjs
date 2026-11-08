import { readFileSync } from "node:fs";
const html = readFileSync(process.argv[2] || new URL("./mission_control.html", import.meta.url), "utf8");      // v10.1: defaults for a bare run
const js = [...html.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/g)].map(m => m[1]).join("\n");
if (!process.argv[3]) { console.log("usage: node render_check.mjs [mission_control.html] <snapshot.json>   (the Dashboard check passes a real snapshot)"); process.exit(2); }
const snap = JSON.parse(readFileSync(process.argv[3], "utf8"));
const el = () => ({ innerHTML: "", textContent: "", style: {}, dataset: {}, classList: { add(){}, remove(){}, toggle(){} }, setAttribute(){}, addEventListener(){}, appendChild(){}, focus(){}, querySelector: () => el(), querySelectorAll: () => [] });
globalThis.document = { querySelector: () => el(), querySelectorAll: () => [], addEventListener(){}, getElementById: () => el(), createElement: () => el(), body: el(), documentElement: el(), visibilityState: "visible" };
globalThis.window = { addEventListener(){}, scrollTo(){}, matchMedia: () => ({ matches: false, addEventListener(){} }), open(){} };
globalThis.location = { protocol: "https:", hash: "" }; globalThis.localStorage = { getItem: () => null, setItem(){} }; Object.defineProperty(globalThis, "navigator", { value: { vibrate(){} }, configurable: true });
globalThis.fetch = async () => ({ status: 200, ok: true, json: async () => snap });
globalThis.errors = [];
const harness = js.replace(/\bload\(\);?\s*$/m, "") + `
;(async () => {
  try { S = await API.snapshot(); } catch (e) { errors.push("snapshot: " + e.message); }
  for (const t of ["docket", "progress", "lab", "money", "controls"]) {
    try { tab = t; render(); } catch (e) { errors.push(t + ": " + e.message); }
  }
  console.log(errors.length ? "RENDER ERRORS:\\n" + errors.join("\\n") : "ALL TABS RENDERED"); process.exit(0);
})();`;
globalThis.process = process; try { new Function(harness)(); } catch (e) { console.log("SCRIPT ERROR: " + e.message); }
