// SPDX-License-Identifier: MIT
// OFFLINE CHECK: the demo is ONE file that works from file:// with the network off. Opens it offline, visits every
// state, presses the keys you list in each, and counts every request other than the file itself (data: and blob: are
// inline, not requests). Target: 0 requests, 0 failed loads, 0 page errors. Also checks that every font the page
// uses has loaded (document.fonts), so a missing embedded face shows up here and not on the booth laptop.
//
//   node offline_check.mjs DEMO.html [--states states.txt] [--keys "ArrowRight*40,l,ArrowRight*40"] [--fonts-only]
//
// Run it with FONTCONFIG_FILE pointing at a config that hides your locally installed brand fonts
// (fonts-embedded-only.conf), so the page can only use what it embeds, as on a borrowed laptop.
import fs from 'node:fs';
import path from 'node:path';
import { playwright } from './clip_check.mjs';

const args = process.argv.slice(2); const opt = (k, d) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : d; };
const file = path.resolve(args[0] || ''); if (!args[0] || !fs.existsSync(file)) { console.error('usage: node offline_check.mjs DEMO.html [--states f] [--keys k]'); process.exit(2); }
const self = 'file://' + file;
const states = opt('--states') ? fs.readFileSync(opt('--states'), 'utf8').split('\n').map((l) => l.trim()).filter((l) => l && !l.startsWith('//')) : [''];
const keys = (opt('--keys', '') || '').split(',').filter(Boolean).flatMap((k) => { const [key, n] = k.split('*'); return Array(+(n || 1)).fill(key); });
const { chromium } = playwright(); const b = await chromium.launch();
const ctx = await b.newContext({ viewport: { width: 1920, height: 1080 } }); await ctx.setOffline(true);
const reqs = [], failed = [], errs = [], badFonts = new Set();
ctx.on('request', (r) => { const u = r.url(); if (!/^(data|blob):/.test(u) && u.split(/[?#]/)[0] !== self) reqs.push(u); });
ctx.on('requestfailed', (r) => { const u = r.url(); if (!/^(data|blob):/.test(u)) failed.push(u); });
const p = await ctx.newPage(); p.on('pageerror', (e) => errs.push(String(e)));
for (const s of states) {
  await p.goto('about:blank'); await p.goto(self + s, { waitUntil: 'load' }); await p.waitForTimeout(800);
  for (const k of keys) { await p.keyboard.press(k); await p.waitForTimeout(120); }
  await p.evaluate(() => document.fonts.ready);
  for (const f of await p.evaluate(() => [...document.fonts].filter((f) => f.status === 'error').map((f) => f.family))) badFonts.add(f);
}
const size = fs.statSync(file).size; await b.close();
const ok = !reqs.length && !failed.length && !errs.length && !badFonts.size;
console.log(`${ok ? 'PASS' : 'FAIL'} offline: ${path.basename(file)} ${(size / 1048576).toFixed(2)} MB, ${states.length} states, ${keys.length} key presses each; ` +
  `requests ${reqs.length}, failed ${failed.length}, page errors ${errs.length}, fonts failed ${badFonts.size}` +
  (reqs.length || failed.length ? `; e.g. ${reqs.concat(failed).slice(0, 3).join(' ')}` : '') + (errs.length ? `; ${errs[0]}` : '') +
  (badFonts.size ? `; ${[...badFonts].join(', ')}` : ''));
process.exit(ok ? 0 : 1);
