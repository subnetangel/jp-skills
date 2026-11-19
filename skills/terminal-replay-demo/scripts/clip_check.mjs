// SPDX-License-Identifier: MIT
// CLIP CHECK: no text and no control may be cut, at the presenter's real window size, in every theme and state.
//
//   node clip_check.mjs DEMO.html --states states.txt --scrollers ".tbody,.log" [--viewports 1688x1130,1920x1080,1280x800]
//        [--modes "dark=,light=&theme=light"] [--wait 400] [--root body]
//
// states.txt: one state per line, appended to the file URL (e.g. "#run/close/approve" or "?step=3"). '//' lines are comments.
// A state fails when:
//  - a visible text run or a control's whole box (button, input, select, textarea, link, role=button) is cut by the
//    edge of an ancestor that hides its overflow (hidden, clip), or by an auto/scroll ancestor that is NOT one of the
//    designated --scrollers. macOS hides scrollbars by default, so a box under an 'auto' edge looks simply cut there:
//    a control row inside a scrolling card body is a clip, even though it "scrolls";
//  - the viewport cuts it.
// Content scrolled out of view inside a designated scroller (the terminal's scrollback) is not a clip. Text cut with an
// ellipsis is counted apart. Runs offline, with reduced motion so states settle. Exit 1 on any hit.
// Playwright: resolved from node_modules, then $PLAYWRIGHT_DIR, then ~/.npm/_npx/*/node_modules/playwright.
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
export function playwright() {
  try { return require('playwright'); } catch { /* next */ }
  if (process.env.PLAYWRIGHT_DIR) return require(process.env.PLAYWRIGHT_DIR);
  const npx = path.join(os.homedir(), '.npm/_npx');
  for (const d of fs.existsSync(npx) ? fs.readdirSync(npx) : []) {
    const p = path.join(npx, d, 'node_modules/playwright'); if (fs.existsSync(p)) return require(p);
  }
  throw new Error('playwright not found: npm i -D playwright && npx playwright install chromium');
}

/** Runs in the page. Returns { runs, boxes, hits, ellipsis }. */
export function clip({ root: rootSel, scrollers }) {
  const SCR = scrollers || '.__none__';
  const root = document.querySelector(rootSel || 'body') || document.body;
  const W = innerWidth, H = innerHeight, T = 1; const hits = [], ell = []; let runs = 0, boxes = 0;
  const up = (el) => el.parentElement || (el.getRootNode() instanceof ShadowRoot ? el.getRootNode().host : null);
  const vis = new Map();
  const visible = (el) => {
    if (vis.has(el)) return vis.get(el);
    let v = true; const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden' || +cs.opacity === 0 || el.hidden) v = false;
    else if (/^rect\(0/.test(cs.clip) || (cs.overflow !== 'visible' && el.offsetWidth <= 2 && el.offsetHeight <= 2)) v = false;   // screen-reader-only
    else if (up(el)) v = visible(up(el));
    vis.set(el, v); return v;
  };
  const memo = new Map();
  const clippers = (el) => {
    if (memo.has(el)) return memo.get(el);
    const own = []; const cs = getComputedStyle(el);
    if (el !== document.body && el !== document.documentElement && (cs.overflowX !== 'visible' || cs.overflowY !== 'visible')) {
      const r = el.getBoundingClientRect();
      if (r.width > 2 && r.height > 2) {
        const sx = el.offsetWidth ? r.width / el.offsetWidth : 1, sy = el.offsetHeight ? r.height / el.offsetHeight : 1;
        const bl = parseFloat(cs.borderLeftWidth) * sx, bt = parseFloat(cs.borderTopWidth) * sy;
        const box = { l: r.left + bl, t: r.top + bt, r: r.left + bl + el.clientWidth * sx, b: r.top + bt + el.clientHeight * sy };
        const designated = el.matches(SCR);
        const scY = designated && /auto|scroll/.test(cs.overflowY), scX = designated && /auto|scroll/.test(cs.overflowX);
        own.push({ el, box, x: cs.overflowX !== 'visible' && !scX, y: cs.overflowY !== 'visible' && !scY, sx: scX, sy: scY, ell: cs.textOverflow === 'ellipsis' });
      }
    }
    const all = own.concat(up(el) ? clippers(up(el)) : []); memo.set(el, all); return all;
  };
  const name = (el) => el.tagName.toLowerCase() + (typeof el.className === 'string' && el.className ? '.' + el.className.split(' ')[0] : '');
  const judge = (q, el, what) => {
    if (clippers(el).some((c) => (c.sy && (q.bottom <= c.box.t + T || q.top >= c.box.b - T)) || (c.sx && (q.right <= c.box.l + T || q.left >= c.box.r - T)))) return null;
    if (q.right <= 0 || q.bottom <= 0 || q.left >= W || q.top >= H) return null;   // a panel slid wholly off screen
    if (q.left < -T || q.top < -T || q.right > W + T || q.bottom > H + T) return `${what} cut by the viewport`;
    for (const c of clippers(el)) {
      if (c.el === el) continue;
      const out = (c.x && (q.left < c.box.l - T || q.right > c.box.r + T)) || (c.y && (q.top < c.box.t - T || q.bottom > c.box.b + T));
      if (!out) continue;
      if (c.ell) { ell.push(`${name(c.el)} ${what}`); return null; }
      return `${what} cut by ${name(c.el)}`;
    }
    return null;
  };
  const roots = [root]; for (let k = 0; k < roots.length; k++) roots[k].querySelectorAll('*').forEach((e) => e.shadowRoot && roots.push(e.shadowRoot));
  const rng = document.createRange();
  for (const rt of roots) {
    for (let tw = document.createTreeWalker(rt, NodeFilter.SHOW_TEXT), n; (n = tw.nextNode());) {
      const txt = n.nodeValue.trim(); if (!txt) continue;
      const el = n.parentElement; if (!el || !visible(el) || el.closest('script,style,noscript,template')) continue;
      { const d = el.closest('details'); if (d && !d.open && !el.closest('summary')) continue; }
      rng.selectNodeContents(n);
      const ecs = getComputedStyle(el), ebr = el.getBoundingClientRect();
      const lh = parseFloat(ecs.lineHeight) * (el.offsetHeight ? ebr.height / el.offsetHeight : 1);   // line boxes, not the font's content area
      for (const q0 of rng.getClientRects()) {
        const q = lh && q0.height > lh ? { left: q0.left, right: q0.right, width: q0.width, height: lh, top: q0.top + (q0.height - lh) / 2, bottom: q0.bottom - (q0.height - lh) / 2 } : q0;
        if (q.width < 0.5 || q.height < 0.5) continue; runs++;
        const bad = judge(q, el, `"${txt.slice(0, 60)}"`); if (bad) { hits.push(bad); break; }
      }
    }
    for (const el of rt.querySelectorAll('button, input, select, textarea, a[href], [role="button"]')) {
      if (!visible(el)) continue; const q = el.getBoundingClientRect(); if (q.width < 4 || q.height < 4) continue; boxes++;
      const bad = judge(q, el, `[${name(el)} "${(el.textContent || el.getAttribute('aria-label') || el.value || '').trim().slice(0, 40)}"]`); if (bad) hits.push(bad);
    }
  }
  return { runs, boxes, hits: [...new Set(hits)], ellipsis: [...new Set(ell)] };
}

async function main() {
  const args = process.argv.slice(2); const opt = (k, d) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : d; };
  const file = args[0]; if (!file || file.startsWith('--')) { console.error('usage: node clip_check.mjs DEMO.html --states states.txt --scrollers SEL'); process.exit(2); }
  const states = fs.readFileSync(opt('--states'), 'utf8').split('\n').map((l) => l.trim()).filter((l) => l && !l.startsWith('//'));
  if (!states.length) { console.error('FAIL clip: no states to check'); process.exit(2); }
  const viewports = opt('--viewports', '1688x1130,1920x1080,1280x800').split(',').map((v) => v.split('x').map(Number));
  const modes = opt('--modes', 'default=').split(',').map((m) => m.split('='));
  const wait = +opt('--wait', 400); const scrollers = opt('--scrollers', ''); const root = opt('--root', 'body');
  const base = 'file://' + path.resolve(file);
  const { chromium } = playwright(); const b = await chromium.launch();
  const hits = {}; let views = 0, runs = 0, boxes = 0, ell = 0; const errs = [];
  for (const [w, h] of viewports) for (const [mode, q] of modes) {
    const ctx = await b.newContext({ viewport: { width: w, height: h }, reducedMotion: 'reduce' }); await ctx.setOffline(true);
    const p = await ctx.newPage(); p.on('pageerror', (e) => errs.push(String(e)));
    for (const s of states) {
      const u = s.startsWith('#') ? `${base}${q ? '?' + q.replace(/^&/, '') : ''}${s}` : `${base}${s}${q}`;
      await p.goto('about:blank'); await p.goto(u); await p.waitForTimeout(wait);
      const r = await p.evaluate(clip, { root, scrollers }); views++; runs += r.runs; boxes += r.boxes; ell += r.ellipsis.length;
      for (const x of r.hits) (hits[x] ||= []).push(`${s} ${w}x${h} ${mode}`);
    }
    await ctx.close();
  }
  await b.close();
  const n = Object.keys(hits).length;
  for (const [k, v] of Object.entries(hits)) console.log(`CUT ${k}  (${v.length} views, e.g. ${v[0]})`);
  console.log(`${n ? 'FAIL' : 'PASS'} clip: ${views} state views (${states.length} states x ${viewports.length} viewports x ${modes.length} modes), ${runs} text runs, ${boxes} control boxes; ${n} distinct cuts; ${ell} ellipsis cuts (by design, not counted); page errors ${errs.length}`);
  process.exit(n || errs.length ? 1 : 0);
}
if (import.meta.url === `file://${process.argv[1]}`) await main();
