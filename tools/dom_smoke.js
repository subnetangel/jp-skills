#!/usr/bin/env node
// SPDX-License-Identifier: MIT
// Optional DOM smoke test for the built demo-engine example and the terminal-replay example, without a browser.
// Needs jsdom, installed anywhere outside the repo:  npm i jsdom   then  NODE_PATH=<that>/node_modules node tools/dom_smoke.js
// It drives keys, clicks and URL modes in a simulated DOM. It proves the wiring, not the look: layout, fonts and
// motion still need a real browser. Exit 0 when every check passes.
'use strict';
const path = require('path');
const { JSDOM } = require('jsdom');
const ROOT = path.resolve(__dirname, '..');
const DEMO = path.join(ROOT, 'templates/demo-engine/example/acme-ledger-demo.html');
const REPLAY = path.join(ROOT, 'skills/terminal-replay/examples/out/acme-ledger-replay.html');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let fails = 0, passes = 0;
function ok(cond, msg) { if (cond) { passes++; console.log('  PASS ' + msg); } else { fails++; console.log('  FAIL ' + msg); } }

async function open(file, query, url) {
  // A file:// URL in jsdom has an opaque origin and refuses history.replaceState; a browser does not. The deck
  // template uses replaceState, so its tests load under a placeholder https URL (nothing is fetched: it's inline).
  const dom = await JSDOM.fromFile(file, {
    url: (url || 'file://' + file) + (query || ''), runScripts: 'dangerously', pretendToBeVisual: true,
    beforeParse(w) {
      w.matchMedia = () => ({ matches: false, addListener() {}, addEventListener() {} });
      w.HTMLElement.prototype.scrollTo = function () {};
    },
  });
  await sleep(50);
  return dom.window;
}
const key = (w, k, o) => (w.document.activeElement || w.document.body).dispatchEvent(new w.KeyboardEvent('keydown', Object.assign({ key: k, bubbles: true }, o || {})));
const on = (w) => [...w.document.querySelectorAll('.slide')].findIndex((s) => s.classList.contains('on')) + 1;
async function until(fn, ms) { const t = Date.now(); while (Date.now() - t < ms) { if (fn()) return true; await sleep(50); } return fn(); }

(async () => {
  console.log('demo-engine, staffed');
  let w = await open(DEMO, '?mode=staffed&speed=8');
  const d = w.document;
  ok(d.querySelectorAll('.slide').length === 8, '8 slides');
  ok(on(w) === 1, 'opens on slide 1');
  key(w, 'ArrowRight'); ok(on(w) === 2, 'ArrowRight goes to slide 2');
  key(w, 'End'); ok(on(w) === 8, 'End goes to the last slide');
  key(w, 'Home'); ok(on(w) === 1, 'Home goes to the first slide');
  key(w, '3'); ok(on(w) === 3, 'number key 3 jumps to slide 3');
  ok(w.location.hash === '#3', 'URL hash follows the slide');
  ok(d.getElementById('counter').textContent === '3 / 8', 'counter reads 3 / 8');
  key(w, 'g'); ok(d.getElementById('picker').classList.contains('open') && d.querySelectorAll('#picker-grid button').length === 8, 'G opens the picker with 8 slides');
  key(w, 'Escape'); ok(!d.getElementById('picker').classList.contains('open'), 'Esc closes the picker');
  const th = d.documentElement.getAttribute('data-theme'); key(w, 'l');
  ok(d.documentElement.getAttribute('data-theme') !== th, 'L switches the theme');
  key(w, '4');
  ok(!!d.querySelector('.slide.on .tp .tp-badge') && /Recreated, not live/.test(d.querySelector('.slide.on .tp-badge').textContent), 'slide 4 shows the terminal with the recreated badge');
  ok(await until(() => d.querySelectorAll('.slide.on .tp-chip').length === 3, 8000), 'approve, decline and inject chips appear');
  [...d.querySelectorAll('.slide.on .tp-chip')].find((b) => /Inject/.test(b.textContent)).click();
  ok(await until(() => d.querySelector('.slide.on .tp').dataset.scene === 'fault', 2000), 'inject plays the failure scene');
  ok(await until(() => [...d.querySelectorAll('.slide.on .tp-chip')].some((b) => /Approve/.test(b.textContent)), 6000), 'the failure returns to the approval');
  [...d.querySelectorAll('.slide.on .tp-chip')].find((b) => /Approve/.test(b.textContent)).click();
  ok(await until(() => /posted/.test(d.querySelector('.slide.on .tp-lines').textContent) && d.querySelector('.slide.on .tp').dataset.scene === 'post', 6000), 'approve posts');
  key(w, '5'); d.querySelector('[data-open-report]').click();
  ok(d.getElementById('report').classList.contains('open') && /Close report/.test(d.getElementById('report-human').textContent), 'report opens in Human view');
  d.querySelector('#report [data-tab="json"]').click();
  ok(!d.getElementById('panel-json').hidden && /"kind"/.test(d.getElementById('report-json').textContent), 'Machine view shows the JSON');
  d.getElementById('zoom-in').click(); ok(d.getElementById('zoom-val').textContent === '110%', 'zoom in reads 110%');
  key(w, 'Escape'); ok(!d.getElementById('report').classList.contains('open'), 'Esc closes the report');
  key(w, 's', { ctrlKey: true, altKey: true }); ok(d.getElementById('staff').classList.contains('open') && !d.getElementById('staff-gate').hidden, 'staff chord opens the code prompt');
  d.getElementById('staff-code').value = '1111'; d.getElementById('staff-ok').click();
  ok(/did not match/.test(d.getElementById('staff-msg').textContent), 'a wrong code is refused');
  d.getElementById('staff-code').value = '0000'; d.getElementById('staff-ok').click();
  ok(!d.getElementById('staff-body').hidden && d.querySelectorAll('[data-setmode]').length === 4, 'the placeholder code unlocks the panel with four modes');
  ok(/^[0-9a-f]{64}$/.test(w.DEMO_CONFIG.staffCodeSha256) && !/['"]0000['"]/.test(require('fs').readFileSync(DEMO, 'utf8')), 'only the hash is in the file, not the code');
  w.close();

  console.log('demo-engine, kiosk with ?idle=1');
  w = await open(DEMO, '?mode=kiosk&idle=1');
  ok(w.document.getElementById('gearbtn').offsetParent === null || getComputedStyleHidden(w, 'gearbtn'), 'staff button hidden in kiosk');
  key(w, 'g'); ok(!w.document.getElementById('picker').classList.contains('open'), 'picker does not open in kiosk');
  key(w, '3'); ok(on(w) === 3, 'visitors can still move');
  ok(await until(() => on(w) === 1, 4000), 'idle returns to slide 1');
  w.close();

  console.log('demo-engine, wall loop');
  w = await open(DEMO, '?mode=wall&playlist=short');
  ok(on(w) === 1, 'the loop starts at its first item');
  key(w, 'ArrowRight'); ok(on(w) === 1, 'keys do not move the wall loop');
  ok(!w.document.getElementById('pausebtn').hidden, 'the loop has a pause control');
  w.document.getElementById('pausebtn').click(); ok(w.document.getElementById('pausebtn').getAttribute('aria-pressed') === 'true', 'pause control pauses the loop');
  w.close();

  console.log('terminal-replay page');
  w = await open(REPLAY, '?speed=8');
  const r = w.document;
  ok(/Recreated, not live/.test(r.querySelector('.tp-badge').textContent), 'badge shown');
  ok(r.querySelectorAll('#tbody tr').length >= 2, 'timing table filled');
  ok(await until(() => r.querySelectorAll('.tp-chip').length === 3, 8000), 'chips appear at the gate');
  [...r.querySelectorAll('.tp-chip')].find((b) => /Decline/.test(b.textContent)).click();
  ok(await until(() => /declined/.test(r.querySelector('.tp-lines').textContent), 3000), 'decline plays the declined scene');
  w.close();

  console.log('worked-example deck');
  const DECK = path.join(ROOT, 'examples/acme-ledger/built/acme-ledger.html');
  const SHARE = path.join(ROOT, 'examples/acme-ledger/built/acme-ledger-share.html');
  w = await open(DECK, '', 'https://deck.example/acme-ledger.html');
  const k = w.document;
  const act = () => [...k.querySelectorAll('.slide')].findIndex((s) => s.classList.contains('active')) + 1;
  ok(k.querySelectorAll('.slide').length === 7, 'deck has 7 slides (10 or fewer)');
  key(w, 'ArrowRight'); ok(act() === 2, 'ArrowRight on a slide with no builds goes to slide 2');
  const before = k.querySelectorAll('#s2 .b.on').length; key(w, 'ArrowRight');
  ok(act() === 2 && k.querySelectorAll('#s2 .b.on').length > before, 'the next press steps a build on slide 2');
  key(w, 'n'); ok(k.getElementById('notes') && k.getElementById('notes').classList.contains('open') && /The problem/.test(k.getElementById('notes-body').textContent), 'N opens the speaker notes for the slide');
  w.close();
  w = await open(SHARE, '', 'https://deck.example/acme-ledger-share.html');
  ok(!w.document.getElementById('notes') && !/NOTES:BEGIN/.test(require('fs').readFileSync(SHARE, 'utf8')), 'share build has no notes');
  w.close();

  console.log(`\nDOM SMOKE: ${passes} passed, ${fails} failed`);
  process.exit(fails ? 1 : 0);
})();

function getComputedStyleHidden(w, id) { const e = w.document.getElementById(id); return e.hidden || w.getComputedStyle(e).display === 'none'; }
