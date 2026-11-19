// SPDX-License-Identifier: MIT
// Runtime smoke test for decks built from assets/deck-template.html, in headless Chromium (Playwright).
// Checks: no page errors; ArrowRight walks every build of every slide in order (read from data-len);
// ArrowLeft returns to the previous slide's last build; number keys jump; L, the corner button,
// ?theme= and the saved choice drive the theme; ?still shows final states; N opens notes only in the
// presenter build; ? opens help; print shows every slide.
// Optional --shots DIR writes DIR/slide-N-<theme>.png stills (final states) for a visual review.
//
// Usage: node scripts/runtime_check.js dist/talk.html [dist/talk-share.html ...] [--shots review]
// Needs Playwright:  npm i -D playwright && npx playwright install chromium   (or set PLAYWRIGHT_PATH)
const path = require('path');
const fs = require('fs');

function loadPlaywright() {
  const tries = [process.env.PLAYWRIGHT_PATH, 'playwright'].filter(Boolean);
  for (const t of tries) { try { return require(require.resolve(t, { paths: [process.cwd(), __dirname] })); } catch (_) {} }
  throw new Error('playwright not found: npm i -D playwright && npx playwright install chromium, or set PLAYWRIGHT_PATH');
}

(async () => {
  const args = process.argv.slice(2);
  const si = args.indexOf('--shots');
  const shots = si >= 0 ? args.splice(si, 2)[1] : null;
  const { chromium } = loadPlaywright();
  const browser = await chromium.launch();
  let failures = 0;
  for (const file of args) {
    const ctx = await browser.newContext({ viewport: { width: 1920, height: 1080 } });
    const page = await ctx.newPage();
    const errors = [];
    page.on('pageerror', (e) => errors.push(String(e)));
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
    const url = 'file://' + path.resolve(file);
    await page.goto(url + '#1');
    await page.waitForTimeout(400);
    const checks = [];
    const active = () => page.$$eval('.slide.active', (els) => els.map((e) => e.id).join(','));
    // builds shown on a slide = its data-pos + 1 (the template sets data-pos on every step, hooks included)
    const shown = (id) => page.$eval(`#${id}`, (e) => (e.dataset.pos === undefined ? 0 : +e.dataset.pos + 1));
    const theme = () => page.getAttribute('html', 'data-theme');
    const press = async (k, n = 1) => { for (let i = 0; i < n; i++) { await page.keyboard.press(k); await page.waitForTimeout(80); } await page.waitForTimeout(200); };
    const slides = await page.$$eval('.slide', (els) => els.map((e) => ({ id: e.id, len: +(e.dataset.len || 0) })));
    const total = slides.length, builds = slides.reduce((a, s) => a + s.len, 0);

    checks.push(['slide 1 active, dark by default', (await active()) === slides[0].id && (await theme()) === 'dark']);
    let walkOk = true;
    for (let n = 0; n < total; n++) {
      if (n > 0) await press('ArrowRight');
      if ((await active()) !== slides[n].id) { walkOk = false; console.log('  expected', slides[n].id, 'got', await active()); break; }
      for (let k = 0; k < slides[n].len; k++) {
        if (k > 0) await press('ArrowRight');
        const got = await shown(slides[n].id);
        if (got !== k + 1) { walkOk = false; console.log(`  ${slides[n].id} build ${k}: ${got} on`); }
      }
    }
    checks.push([`ArrowRight walks every build of all ${total} slides in order (${builds} builds)`, walkOk]);
    await press('ArrowRight');
    checks.push(['ArrowRight on the last slide stays there', (await active()) === slides[total - 1].id]);
    await press('ArrowLeft');
    const prevIdx = slides[total - 1].len > 1 ? total - 1 : total - 2;
    const prevLen = slides[prevIdx].len;
    checks.push(['ArrowLeft steps back one build or to the previous slide at its last build',
      (await active()) === slides[prevIdx].id && (prevLen === 0 || (await shown(slides[prevIdx].id)) === (prevIdx === total - 1 ? prevLen - 1 : prevLen))]);
    await press('2');
    checks.push(['key 2 jumps to slide 2 at its first build', (await active()) === slides[1].id && (slides[1].len === 0 || (await shown(slides[1].id)) === 1)]);
    const track = await page.$('#trk');
    if (track) {
      await press('3');
      await page.click('#trk button[data-i="4"]'); await page.waitForTimeout(200);
      checks.push(['clicking a step on the track moves the marker and the detail panel',
        (await page.$eval('#trk', (t) => t.style.getPropertyValue('--i'))) === '4'
        && (await page.$eval('#detail .st.cur', (e) => e.dataset.i)) === '4']);
    }
    await press('l');
    checks.push(['L switches to light and saves it', (await theme()) === 'light' && (await page.evaluate(() => localStorage.getItem('deck-theme'))) === 'light']);
    await page.click('#themebtn'); await page.waitForTimeout(100);
    checks.push(['the corner button switches back to dark', (await theme()) === 'dark']);
    await page.click('#themebtn'); await page.reload(); await page.waitForTimeout(300);
    checks.push(['the saved light choice survives a reload', (await theme()) === 'light']);
    await page.goto(url + '?theme=dark#2'); await page.waitForTimeout(300);
    checks.push(['?theme=dark overrides the saved choice', (await theme()) === 'dark']);
    const lastBuilt = slides.findIndex((s) => s.len > 1);
    await page.goto(`${url}?still#${lastBuilt + 1}`); await page.waitForTimeout(300);
    checks.push(['?still hides the chrome and shows a slide complete',
      (await page.$eval('#themebtn', (e) => getComputedStyle(e).display)) === 'none' && (await shown(slides[lastBuilt].id)) === slides[lastBuilt].len]);
    await page.keyboard.press('?'); await page.waitForTimeout(100);
    checks.push(['? opens help, which lists the L shortcut', (await page.$eval('#help', (e) => e.classList.contains('open'))) && /Light or dark theme/.test(await page.textContent('#help'))]);
    await page.keyboard.press('Escape');
    await page.goto(url + '#1'); await page.waitForTimeout(300);
    await page.keyboard.press('n'); await page.waitForTimeout(450);
    const hasNotes = await page.evaluate(() => !!document.getElementById('notes'));
    const notesOpen = await page.evaluate(() => !!document.querySelector('.notes.open'));
    const notesText = hasNotes ? (await page.textContent('#notes-body')).length : 0;
    const isShare = /-share\.html$/.test(file);
    checks.push([isShare ? 'share build: no notes panel in the file, N does nothing' : 'presenter build: N opens notes with text',
      isShare ? !hasNotes && !notesOpen : notesOpen && notesText > 100]);
    checks.push(['no page errors', errors.length === 0]);
    await page.emulateMedia({ media: 'print' });
    const printed = await page.evaluate(() => [...document.querySelectorAll('.slide')].filter((e) => getComputedStyle(e).visibility === 'visible').length);
    checks.push([`print shows all ${total} slides`, printed === total]);
    await page.emulateMedia({ media: 'screen' });

    if (shots && !isShare) {
      fs.mkdirSync(shots, { recursive: true });
      for (const t of ['dark', 'light']) {
        for (let n = 1; n <= total; n++) {
          await page.goto(`${url}?still&theme=${t}#${n}`); await page.waitForTimeout(350);
          await page.screenshot({ path: path.join(shots, `slide-${n}-${t}.png`) });
        }
      }
      console.log(`  stills written to ${shots}`);
    }
    console.log(path.basename(file));
    for (const [name, ok] of checks) { console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${name}`); if (!ok) failures++; }
    if (errors.length) console.log('  errors:', errors.slice(0, 5));
    await ctx.close();
  }
  await browser.close();
  process.exit(failures ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(2); });
