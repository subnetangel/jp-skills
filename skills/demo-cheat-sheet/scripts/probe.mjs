#!/usr/bin/env node
// SPDX-License-Identifier: MIT
// Offline probe for a booth demo: open it from file:// with every non-file request blocked,
// run optional steps, and record what it tried to fetch, errors, screenshots and visible text.
// Usage: node probe.mjs <demo.html> <outDir> [steps.json]   (PROBE_VIEWPORT=1920x1080 to change the 1600x900 default)
// steps.json: [{"key":"ArrowRight","times":3,"gap":800}, {"text":"Start the tour"}, {"click":"#id"},
//              {"mouse":true}, {"wait":2000}, {"shot":"name"}]  (keys combine in one step)
import { createRequire } from 'node:module';
import { execSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

const require = createRequire(import.meta.url);
function playwright() {
  try { return require('playwright'); } catch { /* fall back to the npx cache */ }
  const p = execSync('ls -d ~/.npm/_npx/*/node_modules/playwright 2>/dev/null | head -1', { shell: '/bin/bash' }).toString().trim();
  if (!p) throw new Error('playwright not found: run `npx playwright install chromium` once');
  return require(p);
}

const [file, outDir, stepsFile] = process.argv.slice(2);
if (!file || !outDir) { console.error('usage: node probe.mjs <demo.html> <outDir> [steps.json]'); process.exit(2); }
const steps = stepsFile ? JSON.parse(fs.readFileSync(stepsFile, 'utf8')) : [];
fs.mkdirSync(outDir, { recursive: true });
const log = { file: path.resolve(file), local: 0, blocked: [], consoleErrors: [], pageErrors: [], stepErrors: [], shots: [] };

const browser = await playwright().chromium.launch();
const [vw, vh] = (process.env.PROBE_VIEWPORT || '1600x900').split('x').map(Number);
const ctx = await browser.newContext({ viewport: { width: vw, height: vh }, offline: true });
await ctx.route('**/*', (route) => {
  const u = route.request().url();
  if (/^(file|data|blob):/.test(u)) { log.local += 1; return route.continue(); }
  log.blocked.push(u.slice(0, 200));
  return route.abort();
});
const page = await ctx.newPage();
page.on('console', (m) => { if (m.type() === 'error') log.consoleErrors.push(m.text().slice(0, 200)); });
page.on('pageerror', (e) => log.pageErrors.push(String(e).slice(0, 200)));

const shot = async (name) => { const p = path.join(outDir, `${String(log.shots.length).padStart(2, '0')}-${name}.png`); await page.screenshot({ path: p }); log.shots.push(p); };
await page.goto('file://' + path.resolve(file), { waitUntil: 'load' });
await page.waitForTimeout(2500);
await shot('load');
for (const [i, s] of steps.entries()) {
  try {
    if (s.mouse) { await page.mouse.move(300, 300); await page.mouse.move(800, 500, { steps: 5 }); }
    // DOM click by visible text: works when overlays make Playwright's actionability checks time out.
    if (s.text) {
      // Visible = has a box and is not hidden; offsetParent alone misses position:fixed overlays.
      const hit = await page.evaluate((t) => {
        const el = [...document.querySelectorAll('button,a,[role=button]')].find((b) => {
          const r = b.getBoundingClientRect(), cs = getComputedStyle(b);
          return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none' && b.textContent.includes(t);
        });
        el?.click(); return !!el;
      }, s.text);
      if (!hit) log.stepErrors.push(`step ${i}: no visible button with text "${s.text}"`);
    }
    if (s.click) await page.click(s.click, { timeout: 3000 });
    if (s.key) for (let n = 0; n < (s.times ?? 1); n++) { await page.keyboard.press(s.key); await page.waitForTimeout(s.gap ?? 300); }
    await page.waitForTimeout(s.wait ?? 1200);
    if (s.shot) await shot(s.shot);
  } catch (e) { log.stepErrors.push(`step ${i}: ${String(e).slice(0, 160)}`); }
}
log.title = await page.title();
fs.writeFileSync(path.join(outDir, 'text.txt'), await page.evaluate(() => document.body.innerText));
fs.writeFileSync(path.join(outDir, 'probe.json'), JSON.stringify(log, null, 2));
console.log(JSON.stringify({ title: log.title, local: log.local, blocked: log.blocked, consoleErrors: log.consoleErrors.length, pageErrors: log.pageErrors.length, stepErrors: log.stepErrors }, null, 1));
await browser.close();
