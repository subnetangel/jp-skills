// SPDX-License-Identifier: MIT
// Extract every click-through build state of a deck made from assets/deck-template.html as NATIVE drawing records.
// One JSON file per state, per theme, plus a reference still of the same state (for comparing against the PPTX).
//
// Per record: geometry and colours from the live page, plus
//   z      paint order (DOM index of the owning element; stable across states, so lifetimes keep the browser's z-order)
//   meta   the HTML build that reveals it: build index (data-b), motion kind (float/fly/zoom/wipe/fade), offsets, scale,
//          delay and durations, read from the template's build classes before transitions are frozen
//   flags  mover (moving marker), grow (filling bar), spin (ambient comet), ping (gate beat), count (count-up)
// plus `particles` (flow dots that loop along a wire) per state.
//
// Template build classes understood (see references/deck-workflow.md):
//   .b (float up 16 px) · .b.pop (zoom from 86 %) · .b.from-l / .b.from-r (fly 36 px) · .stag > * (float 12 px, staggered)
//   .draw (wipe in the stroke's direction) · .swap .now (fly 30 px from the left) · .trk .mark (motion path)
//   .trk .fill (wipe from left) · .comet (spin) · [data-count] (final value + emphasis) · .wire .pt (looping motion path)
// Any element can override its motion with data-pptx="fade|float|fly-l|fly-r|fly-up|fly-down|zoom|wipe".
//
// Usage: node dom_extract.js <states.json> <deck.html> <out-dir> <theme>
const fs = require('fs'); const path = require('path');

function loadPlaywright() {
  for (const t of [process.env.PLAYWRIGHT_PATH, 'playwright'].filter(Boolean)) { try { return require(require.resolve(t, { paths: [process.cwd(), __dirname] })); } catch (_) {} }
  console.error('playwright not found: npm i -D playwright && npx playwright install chromium (or set PLAYWRIGHT_PATH)');
  process.exit(3);
}
const { chromium } = loadPlaywright();
const [states, html, out, theme] = [JSON.parse(fs.readFileSync(process.argv[2], 'utf8')), path.resolve(process.argv[3]), process.argv[4], process.argv[5] || 'dark'];
fs.mkdirSync(path.join(out, 'icons'), { recursive: true }); fs.mkdirSync(path.join(out, 'stills'), { recursive: true });

// ---------- pass 1 (live CSS, transitions still defined): build metadata per element ----------
const META = (n) => {
  const root = document.querySelectorAll('.slide')[n - 1];
  const all = [...root.querySelectorAll('*')];
  all.forEach((el, i) => el.setAttribute('data-z', i + 1));
  const cs = (el) => getComputedStyle(el);
  const sec = (v) => parseFloat(v) || 0;
  const OVERRIDE = { fade: { kind: 'fade', dur: 500 }, float: { kind: 'float', dy: 16, dur: 600, fade: 500 }, 'fly-l': { kind: 'fly', dx: -36, dur: 600, fade: 500 },
    'fly-r': { kind: 'fly', dx: 36, dur: 600, fade: 500 }, 'fly-up': { kind: 'fly', dy: 60, dur: 600, fade: 500 }, 'fly-down': { kind: 'fly', dy: -60, dur: 600, fade: 500 },
    zoom: { kind: 'zoom', scale: 0.86, dur: 550, fade: 350 }, wipe: { kind: 'wipe', dur: 1000 } };
  for (const el of all) {
    let m = null, delay = 0, build = null;
    for (let e = el; e && e !== root; e = e.parentElement) {
      delay = Math.max(delay, sec(cs(e).transitionDelay));
      if (!m) {
        if (e.dataset && e.dataset.pptx && OVERRIDE[e.dataset.pptx]) m = { ...OVERRIDE[e.dataset.pptx] };
        else if (e.classList.contains('draw')) m = { kind: 'wipe', dur: 1000 };
        else if (e.matches('.stag>*')) m = { kind: 'float', dy: 12, dur: 550, fade: 450 };
        else if (e.matches('.swap .now')) m = { kind: 'fly', dx: -30, dur: 700, fade: 500 };
        else if (e.classList.contains('b')) {
          const c = e.classList;
          if (e instanceof SVGElement) m = { kind: 'fade', dur: 500 };
          else if (c.contains('pop')) m = { kind: 'zoom', scale: 0.86, dur: 550, fade: 350 };
          else if (c.contains('from-l')) m = { kind: 'fly', dx: -36, dur: 600, fade: 500 };
          else if (c.contains('from-r')) m = { kind: 'fly', dx: 36, dur: 600, fade: 500 };
          else m = { kind: 'float', dy: 16, dur: 600, fade: 500 };
        }
      }
      if (e.classList.contains('b')) { build = +e.dataset.b; break; }
    }
    m = m || { kind: 'fade', dur: 300 };
    m.delay = Math.round(delay * 1000); m.build = build;
    if (el.closest('.trk .mark')) m.mover = 'mark';
    if (el.matches('.trk .fill')) { m.grow = true; m.dur = 600; }
    if (el.closest('.comet')) m.spin = { dur: Math.round(sec(cs(el.closest('.comet')).animationDuration) * 1000) || 9000 };
    if (el.matches('.trk button[data-k="gate"].cur .node')) m.ping = { dur: 1200, count: 2 };
    if (el.closest('[data-count]') || el.querySelector(':scope > [data-count]')) m.count = true;
    el.setAttribute('data-meta', JSON.stringify(m));
  }
  // flow particles: dots that ride a wire with a translateX(var(--run)) keyframe
  const particles = [];
  for (const pt of root.querySelectorAll('.wire .pt')) {
    const wire = pt.closest('.wire'); const wr = wire.getBoundingClientRect(); const s = cs(pt);
    const run = parseFloat(s.getPropertyValue('--run')) || wr.width; const w = pt.offsetWidth;
    const v = (s.backgroundColor.match(/[\d.]+/g) || [0, 0, 0]).map(Number);
    const b = pt.closest('.b');
    particles.push({ build: b ? +b.dataset.b : 0, x0: wr.left + pt.offsetLeft + w / 2, y0: wr.top + pt.offsetTop + w / 2, run, w,
      dur: Math.round(sec(s.animationDuration) * 1000) || 2200, delay: Math.round(sec(s.animationDelay) * 1000),
      color: v.slice(0, 3).map(x => Math.round(x).toString(16).padStart(2, '0')).join('').toUpperCase(), z: +pt.getAttribute('data-z') });
  }
  return particles;
};

// ---------- pass 2 (transitions and animations frozen): geometry ----------
const EXTRACT = (n) => {
  const root = document.querySelectorAll('.slide')[n - 1];
  const cs = (el, p) => getComputedStyle(el, p || null);
  const num = (v) => parseFloat(v) || 0;
  const Z = (el) => +(el.getAttribute('data-z') || 0);
  const META = (el) => JSON.parse(el.getAttribute('data-meta') || '{"kind":"fade","dur":300,"delay":0,"build":null}');
  const visible = (el) => {
    for (let e = el; e && e !== root.parentElement; e = e.parentElement) {
      const s = cs(e); if (s.display === 'none' || s.visibility === 'hidden' || parseFloat(s.opacity) < 0.05) return false;
    }
    const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0 && r.bottom > 0 && r.top < 1080 && r.right > 0 && r.left < 1920;
  };
  const effOpacity = (el) => { let o = 1; for (let e = el; e && e !== root.parentElement; e = e.parentElement) o *= parseFloat(cs(e).opacity); return o; };
  const isInline = (el) => /^inline|^contents/.test(cs(el).display);
  const parseColor = (c) => { const m = (c || '').match(/rgba?\(([^)]+)\)/); if (!m) return { hex: '000000', a: 0 };
    const v = m[1].split(/[\s,\/]+/).filter(x => x !== '').map(x => parseFloat(x)); const h = v.slice(0, 3).map(x => Math.round(x).toString(16).padStart(2, '0')).join('').toUpperCase();
    return { hex: h, a: v.length > 3 ? v[3] : 1 }; };
  const parseShadows = (txt) => {
    if (!txt || txt === 'none') return [];
    const parts = []; let depth = 0, cur = '';
    for (const ch of txt) { if (ch === '(') depth++; if (ch === ')') depth--; if (ch === ',' && !depth) { parts.push(cur); cur = ''; } else cur += ch; }
    parts.push(cur);
    return parts.map(p => { const col = p.match(/rgba?\([^)]+\)/); const rest = p.replace(col ? col[0] : '', '');
      const L = (rest.match(/-?[\d.]+px|\b0\b/g) || []).map(parseFloat); while (L.length < 4) L.push(0);
      return { color: parseColor(col ? col[0] : ''), x: L[0], y: L[1], blur: L[2], spread: L[3], inset: /inset/.test(p) }; });
  };
  const styleOf = (el) => { const s = cs(el); const c = parseColor(s.color);
    return { size: parseFloat(s.fontSize), weight: parseInt(s.fontWeight, 10) || 400, italic: s.fontStyle === 'italic', color: c.hex, alpha: c.a * effOpacity(el),
      family: s.fontFamily, spacing: s.letterSpacing === 'normal' ? 0 : parseFloat(s.letterSpacing), upper: s.textTransform === 'uppercase',
      strike: /line-through/.test(s.textDecorationLine) }; };

  // ---------- shapes ----------
  const shapes = [];
  const boxFrom = (s, r, opacity, tag, z, meta) => {
    const bg = parseColor(s.backgroundColor); bg.a *= opacity;
    const bw = { t: num(s.borderTopWidth), r: num(s.borderRightWidth), b: num(s.borderBottomWidth), l: num(s.borderLeftWidth) };
    const side = { t: 'Top', r: 'Right', b: 'Bottom', l: 'Left' };
    const sideOn = (k) => bw[k] > 0 && s['border' + side[k] + 'Style'] !== 'none' && parseColor(s['border' + side[k] + 'Color']).a > 0.01;
    const on = { t: sideOn('t'), r: sideOn('r'), b: sideOn('b'), l: sideOn('l') };
    const anyBorder = on.t || on.r || on.b || on.l;
    const uniform = on.t && on.r && on.b && on.l && bw.t === bw.r && bw.t === bw.b && bw.t === bw.l;
    const bc = parseColor(s.borderTopColor); bc.a *= opacity;
    const radius = num(s.borderTopLeftRadius);
    const rPct = /%/.test(s.borderTopLeftRadius) ? parseFloat(s.borderTopLeftRadius) : null;
    const shadows = parseShadows(s.boxShadow).map(x => { x.color.a *= opacity; return x; }).filter(x => x.color.a > 0.01);
    const grad = s.backgroundImage && /gradient/.test(s.backgroundImage) ? s.backgroundImage : null;
    if (bg.a < 0.01 && !anyBorder && !shadows.length && !grad) return;
    const rec = { kind: 'rect', x: r.left, y: r.top, w: r.width, h: r.height, tag, z, meta,
      rx: rPct !== null ? Math.min(r.width, r.height) * rPct / 100 : Math.min(radius, Math.min(r.width, r.height) / 2),
      fill: bg.a > 0.01 ? bg : null, stroke: anyBorder && uniform ? { hex: bc.hex, a: bc.a, w: bw.t, dash: s.borderTopStyle === 'dashed' } : null,
      shadows, grad, opacity };
    if (r.rot) rec.rot = r.rot;
    if ((rPct !== null && rPct >= 50 || radius >= Math.min(r.width, r.height) / 2 - 0.5) && Math.abs(r.width - r.height) < 1) rec.kind = 'ellipse';
    shapes.push(rec);
    if (anyBorder && !uniform) {
      const sides = [['t', bw.t, r.left, r.top, r.width, bw.t], ['b', bw.b, r.left, r.bottom - bw.b, r.width, bw.b],
                     ['l', bw.l, r.left, r.top, bw.l, r.height], ['r', bw.r, r.right - bw.r, r.top, bw.r, r.height]];
      for (const [k, w, x, y, ww, hh] of sides) {
        if (!w || !on[k]) continue; const c = parseColor(s['border' + side[k] + 'Color']); c.a *= opacity;
        if (c.a > 0.01) shapes.push({ kind: 'rect', x, y, w: ww, h: hh, rx: 0, fill: c, stroke: null, tag: tag + '::border-' + k, z: z + 0.001, meta, shadows: [] });
      }
    }
  };
  const pseudoBox = (el, which) => {
    const s = cs(el, which); if (!s.content || s.content === 'none' || s.content === 'normal') return;
    if (parseFloat(s.opacity) < 0.05) return;
    const bg = parseColor(s.backgroundColor); const bw = num(s.borderTopWidth);
    if (bg.a < 0.01 && !(bw && parseColor(s.borderTopColor).a > 0.01) && !/gradient/.test(s.backgroundImage)) return;
    if (el === root && which === '::before') return;   // the slide's glow overlay is drawn as the slide background
    const er = el.getBoundingClientRect(); const es = cs(el);
    let x, y, w, h;
    if (s.position === 'absolute') {
      const bl = num(es.borderLeftWidth), bt = num(es.borderTopWidth);
      const cw = er.width - bl - num(es.borderRightWidth), ch = er.height - bt - num(es.borderBottomWidth);
      w = s.width === 'auto' ? cw - num(s.left) - num(s.right) : num(s.width);
      h = s.height === 'auto' ? ch - num(s.top) - num(s.bottom) : num(s.height);
      x = er.left + bl + (s.left !== 'auto' ? num(s.left) : cw - num(s.right) - w);
      y = er.top + bt + (s.top !== 'auto' ? num(s.top) : ch - num(s.bottom) - h);
      if (s.transform && s.transform !== 'none') {   // scaleX bars (progress fills): the drawn width
        const mtx = new DOMMatrix(s.transform); w *= mtx.a; h *= mtx.d;
      }
    } else {
      // static ::before (list dots): place it on the first line of a flex/grid row
      w = num(s.width) || er.width; h = num(s.height) || er.height; x = er.left; y = er.top;
      if (/flex|grid/.test(es.display)) { const lh = num(es.lineHeight) || num(es.fontSize) * 1.2;
        const ty = s.transform && s.transform !== 'none' ? new DOMMatrix(s.transform).f : 0;
        x = er.left + num(es.paddingLeft); y = er.top + num(es.paddingTop) + (es.alignItems === 'baseline' ? (lh - h) / 2 + lh * 0.12 : (er.height - num(es.paddingTop) - num(es.paddingBottom) - h) / 2) + ty; }
    }
    if (w <= 0.5 || h <= 0) return;
    boxFrom(s, { left: x, top: y, width: w, height: h, right: x + w, bottom: y + h }, parseFloat(s.opacity) * effOpacity(el), (el.className && el.className.baseVal === undefined ? el.className : el.tagName) + which, Z(el) + 0.2, META(el));
  };

  // ---------- svg geometry (connectors, arrows) and icons ----------
  const svgShapes = []; const icons = [];
  const GEOM = 'svg.links, svg.wires, svg.arr, svg[data-pptx-geom]';
  const parsePath = (d) => { // absolute and relative M L H V C Z -> one point list per subpath (C keeps its end point)
    const subs = []; let cur = null, cx = 0, cy = 0, sx = 0, sy = 0; const re = /([MLHVCZmlhvcz])\s*([^MLHVCZmlhvcz]*)/g; let m;
    while ((m = re.exec(d))) { const nums = (m[2].match(/-?(?:\d+\.?\d*|\.\d+)(?:e[-+]?\d+)?/gi) || []).map(Number); const c = m[1]; const rel = c === c.toLowerCase();
      const C = c.toUpperCase();
      if (C === 'M') { for (let i = 0; i < nums.length; i += 2) { cx = (rel ? cx : 0) + nums[i]; cy = (rel ? cy : 0) + nums[i + 1];
          if (i === 0) { cur = [[cx, cy]]; subs.push(cur); sx = cx; sy = cy; } else cur.push([cx, cy]); } }
      else if (C === 'L') { for (let i = 0; i < nums.length; i += 2) { cx = (rel ? cx : 0) + nums[i]; cy = (rel ? cy : 0) + nums[i + 1]; cur.push([cx, cy]); } }
      else if (C === 'H') { for (const v of nums) { cx = (rel ? cx : 0) + v; cur.push([cx, cy]); } }
      else if (C === 'V') { for (const v of nums) { cy = (rel ? cy : 0) + v; cur.push([cx, cy]); } }
      else if (C === 'C') { for (let i = 0; i < nums.length; i += 6) { cx = (rel ? cx : 0) + nums[i + 4]; cy = (rel ? cy : 0) + nums[i + 5]; cur.push([cx, cy]); } }
      else if (C === 'Z') { if (cur) cur.push([sx, sy]); cx = sx; cy = sy; } }
    return subs; };
  const inlineUse = (clone, live) => {   // resolve <use href="#id"> so the icon renders on its own page
    for (const u of [...clone.querySelectorAll('use')]) {
      const ref = (u.getAttribute('href') || u.getAttribute('xlink:href') || '').replace(/^#/, '');
      const sym = ref && document.getElementById(ref); if (!sym) continue;
      const g = document.createElementNS('http://www.w3.org/2000/svg', 'g'); g.innerHTML = sym.innerHTML; u.replaceWith(g);
      if (!clone.getAttribute('viewBox') && sym.getAttribute('viewBox')) clone.setAttribute('viewBox', sym.getAttribute('viewBox'));
    }
    if (!clone.getAttribute('viewBox')) { const r = live.getBoundingClientRect(); clone.setAttribute('viewBox', `0 0 ${r.width} ${r.height}`); }
  };
  for (const svg of root.querySelectorAll('svg')) {
    if (!visible(svg)) continue;
    const r = svg.getBoundingClientRect();
    if (svg.matches(GEOM)) {
      for (const el of svg.querySelectorAll('path, line')) {
        const s = cs(el); if (s.display === 'none' || parseFloat(s.opacity) < 0.05) continue;
        if (el.hasAttribute('pathLength') && parseFloat(s.strokeDashoffset) > 0.01) continue;   // a .draw stroke not drawn yet
        const ctm = el.getScreenCTM(); const sc = Math.hypot(ctm.a, ctm.b);
        const stroke = parseColor(s.stroke); stroke.a *= effOpacity(svg) * parseFloat(s.opacity); const sw = num(s.strokeWidth) * sc;
        const dashed = s.strokeDasharray && s.strokeDasharray !== 'none' && !el.hasAttribute('pathLength');
        const st = stroke.a > 0.01 && sw > 0 ? { hex: stroke.hex, a: stroke.a, w: sw, dash: dashed ? s.strokeDasharray.split(/[\s,]+/).map(parseFloat) : null, cap: s.strokeLinecap } : null;
        if (!st) continue;
        const subs = el.tagName === 'line' ? [[[+el.getAttribute('x1'), +el.getAttribute('y1')], [+el.getAttribute('x2'), +el.getAttribute('y2')]]] : parsePath(el.getAttribute('d') || '');
        subs.forEach((pts, si) => {
          const pg = pts.map(([x, y]) => { const pt = svg.createSVGPoint(); pt.x = x; pt.y = y; const q = pt.matrixTransform(ctm); return [q.x, q.y]; });
          const meta = META(el); meta.sub = si; meta.nsub = subs.length;
          svgShapes.push({ kind: 'polyline', points: pg, stroke: st, tag: 'svg-path', z: Z(el) + si * 0.01, meta });
        });
      }
    } else {
      const clone = svg.cloneNode(true); inlineUse(clone, svg);
      clone.setAttribute('width', Math.round(r.width)); clone.setAttribute('height', Math.round(r.height));
      clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg'); clone.removeAttribute('aria-hidden');
      // currentColor resolves to the live colour, so the stand-alone icon matches the theme
      clone.setAttribute('color', cs(svg).color);
      const id = 'icon-' + Math.round(r.left) + '-' + Math.round(r.top) + '-' + Math.round(r.width) + '-' + Math.round(r.height);
      icons.push({ id, x: r.left, y: r.top, w: r.width, h: r.height, svg: clone.outerHTML, tag: 'svg-icon', z: Z(svg), meta: META(svg), opacity: effOpacity(svg) });
    }
  }

  // ---------- raster images (only if a deck adds <img>; the template has none) ----------
  const images = [];
  for (const img of root.querySelectorAll('img')) { if (!visible(img)) continue; const r = img.getBoundingClientRect();
    images.push({ src: img.currentSrc || img.src, x: r.left, y: r.top, w: r.width, h: r.height, opacity: effOpacity(img), z: Z(img), meta: META(img) }); }
  const rs = cs(root);
  const slideBg = { color: parseColor(rs.backgroundColor), gradient: /gradient/.test(rs.backgroundImage) ? rs.backgroundImage : null };
  const before = cs(root, '::before'); const overlay = (before.content && before.content !== 'none' && /gradient/.test(before.backgroundImage)) ? before.backgroundImage : null;

  // ---------- walk boxes ----------
  for (const el of root.querySelectorAll('*')) {
    if (el.closest('svg') || !visible(el) || el.tagName === 'IMG') continue;
    let r = el.getBoundingClientRect();
    const tr = cs(el).transform;
    if (tr && tr !== 'none' && Math.abs(new DOMMatrix(tr).b) > 1e-6) {  // rotated (ring dots): true size about the visual centre
      const cx = r.left + r.width / 2, cy = r.top + r.height / 2, w = el.offsetWidth, h = el.offsetHeight;
      const mx = new DOMMatrix(tr);
      r = { left: cx - w / 2, top: cy - h / 2, width: w, height: h, right: cx + w / 2, bottom: cy + h / 2, rot: Math.atan2(mx.b, mx.a) * 180 / Math.PI };
    }
    boxFrom(cs(el), r, effOpacity(el), el.tagName.toLowerCase() + (el.className ? '.' + String(el.className).split(' ')[0] : ''), Z(el), META(el));
    pseudoBox(el, '::before'); pseudoBox(el, '::after');
  }
  const comet = root.querySelector('.comet'); const spin = comet ? (() => { const r = comet.getBoundingClientRect(); return { x: r.left, y: r.top, w: r.width, h: r.height }; })() : null;

  // ---------- text, with the browser's own line breaks ----------
  const consumed = new Set(); const blocks = [];
  const pushText = (node, style, runs, st) => {
    const raw = node.nodeValue; if (!raw.trim()) { if (runs.length && /\s/.test(raw)) runs[runs.length - 1].text += ' '; return; }
    const re = /\S+/g; let m, outText = '', lastEnd = 0;
    const pieces = (start, tok) => {   // a hyphenated word may wrap at its hyphen: split it there
      const outp = []; let from = 0;
      for (let i = 0; i < tok.length; i++) {
        if (tok[i] === '-' && i < tok.length - 1) {
          const a = document.createRange(); a.setStart(node, start + from); a.setEnd(node, start + i + 1);
          const b = document.createRange(); b.setStart(node, start + i + 1); b.setEnd(node, start + i + 2);
          const ra = a.getClientRects(), rb = b.getClientRects();
          if (ra.length && rb.length && Math.abs(rb[0].top - ra[ra.length - 1].top) > 3) { outp.push({ text: tok.slice(from, i + 1), top: ra[ra.length - 1].top, bot: ra[ra.length - 1].bottom }); from = i + 1; }
        }
      }
      const r = document.createRange(); r.setStart(node, start + from); r.setEnd(node, start + tok.length);
      const rr = r.getClientRects(); outp.push({ text: tok.slice(from), top: rr.length ? rr[0].top : null, bot: rr.length ? rr[0].bottom : null });
      return outp;
    };
    while ((m = re.exec(raw))) {
      const ws = raw.slice(lastEnd, m.index);
      pieces(m.index, m[0]).forEach((pc, pi) => {
        const top = pc.top === null ? st.top : pc.top;
        const bot = pc.bot == null ? (st.bot == null ? top : st.bot) : pc.bot;
        // compare bottoms (near the baseline), scaled by the smaller glyph box: mixed sizes on one line stay one line
        const hh = Math.min(bot - top || 1e9, (st.bot - st.top) || 1e9);
        if (st.top !== null && top !== null && Math.abs(top - st.top) > 3 && Math.abs(bot - st.bot) > 0.45 * hh) {
          outText = outText.replace(/\s+$/, ''); if (!outText && runs.length) runs[runs.length - 1].text = runs[runs.length - 1].text.replace(/\s+$/, '');
          outText += '\n';
        } else if (pi === 0 && ws && (outText || runs.length)) { outText += ' '; }
        outText += style.upper ? pc.text.toUpperCase() : pc.text; st.top = top; st.bot = bot;
      });
      lastEnd = m.index + m[0].length;
    }
    if (/\s$/.test(raw)) outText += ' ';
    runs.push({ ...style, text: outText });
  };
  const collect = (el, runs, st) => {
    for (const ch of el.childNodes) {
      if (ch.nodeType === 3) pushText(ch, styleOf(el), runs, st);
      else if (ch.nodeType === 1 && ch.tagName.toLowerCase() !== 'svg') {
        if (!visible(ch)) { consumed.add(ch); continue; }
        if (isInline(ch)) { consumed.add(ch);
          if (parseFloat(cs(ch).marginLeft) > 2 && runs.length && !/\s$/.test(runs[runs.length - 1].text)) runs[runs.length - 1].text += ' ';
          collect(ch, runs, st); }
      }
    }
  };
  const textRects = (el) => { const rs = []; const walk = (e) => { for (const ch of e.childNodes) {
      if (ch.nodeType === 3 && ch.nodeValue.trim()) { const r = document.createRange(); r.selectNodeContents(ch); for (const b of r.getClientRects()) if (b.width > 0) rs.push(b); }
      else if (ch.nodeType === 1 && isInline(ch) && visible(ch)) walk(ch); } }; walk(el);
    if (!rs.length) return null; const x1 = Math.min(...rs.map(r => r.left)), y1 = Math.min(...rs.map(r => r.top)), x2 = Math.max(...rs.map(r => r.right)), y2 = Math.max(...rs.map(r => r.bottom));
    return { left: x1, top: y1, width: x2 - x1, height: y2 - y1, lineTop: rs[0].top, lineH: rs[0].height }; };
  for (const el of root.querySelectorAll('*')) {
    if (consumed.has(el) || el.closest('svg') || !visible(el)) continue;
    const s = cs(el); const r = el.getBoundingClientRect();
    const pl = num(s.paddingLeft), pr = num(s.paddingRight);
    const direct = [...el.childNodes].some(ch => ch.nodeType === 3 && ch.nodeValue.trim());
    const inlineOnly = [...el.children].length > 0 && [...el.children].every(ch => isInline(ch) || !visible(ch) || ch.tagName.toLowerCase() === 'svg');
    if (!(direct || (inlineOnly && el.textContent.trim()))) continue;
    const runs = [];
    collect(el, runs, { top: null, bot: null });
    while (runs.length && !runs[runs.length - 1].text.trim()) runs.pop();
    if (!runs.length) continue;
    runs[0].text = runs[0].text.replace(/^\s+/, ''); runs[runs.length - 1].text = runs[runs.length - 1].text.replace(/\s+$/, '');
    const lh = s.lineHeight === 'normal' ? parseFloat(s.fontSize) * 1.2 : parseFloat(s.lineHeight);
    const t = textRects(el); if (!t) continue;
    const nLines = runs.map(x => x.text).join('').split('\n').length;
    const flex = /flex/.test(s.display);
    let align = flex ? ({ center: 'c', 'flex-end': 'r', end: 'r' }[s.justifyContent] || 'l') : ({ start: 'l', left: 'l', center: 'c', right: 'r', end: 'r' }[s.textAlign] || 'l');
    if (flex && s.flexDirection === 'column') align = ({ center: 'c', 'flex-end': 'r', end: 'r' }[s.alignItems] || (s.textAlign === 'center' ? 'c' : 'l'));
    let x = r.left + pl, w = r.width - pl - pr;
    if (align === 'l') { x = t.left; w = Math.max(r.right - pr - t.left, t.width); }
    if (align === 'c' && t.width > w) { x = t.left; w = t.width; }
    const y = t.lineTop - (lh - t.lineH) / 2;
    blocks.push({ x, y, w, h: nLines * lh, align, lineHeight: lh, runs, tag: el.tagName.toLowerCase() + (el.className ? '.' + String(el.className).split(' ')[0] : ''), z: Z(el) + 0.5, meta: META(el) });
  }
  const brand = cs(document.documentElement).getPropertyValue('--brand').trim();
  return { w: 1920, h: 1080, slideBg, overlay, shapes, svgShapes, icons, images, blocks, spin, brand };
};

(async () => {
  const b = await chromium.launch();
  const iconsDone = new Set();
  const iconCtx = await b.newContext({ viewport: { width: 600, height: 600 }, deviceScaleFactor: 6 }); const iconPage = await iconCtx.newPage();
  const ctx = await b.newContext({ viewport: { width: 1920, height: 1080 } });
  for (const [n, id, label, k] of states) {
    const p = await ctx.newPage();
    await p.goto(`file://${html}?theme=${theme}#${n}`); await p.waitForTimeout(700);
    for (let i = 0; i < k; i++) { await p.keyboard.press('ArrowRight'); await p.waitForTimeout(220); }
    await p.waitForTimeout(1800);   // every transition, stagger and count-up has finished
    const particles = await p.evaluate(META, n);
    await p.addStyleTag({ content: '*,*::before,*::after{transition:none!important;animation:none!important} .hint,.navbtn,.themebtn,.progress{display:none!important}' });
    await p.waitForTimeout(150);
    await p.screenshot({ path: path.join(out, 'stills', `${id}.png`) });   // reference still of this exact state
    const data = await p.evaluate(EXTRACT, n);
    Object.assign(data, { state: id, slide: n, label, step: k, theme, particles });
    for (const ic of data.icons) {
      if (!iconsDone.has(ic.id)) {
        iconsDone.add(ic.id);
        // rendered alone on a transparent page at 6x, so the PNG fallback carries no slide pixels
        await iconPage.setContent(`<html><body style="margin:0;background:transparent">${ic.svg}</body></html>`);
        const h = await iconPage.$('svg');
        await h.screenshot({ path: path.join(out, 'icons', ic.id + '.png'), omitBackground: true });
        fs.writeFileSync(path.join(out, 'icons', ic.id + '.svg'), ic.svg);
      }
      delete ic.svg;
    }
    fs.writeFileSync(path.join(out, id + '.json'), JSON.stringify(data));
    console.log('extracted', theme, id, `${data.blocks.length} text, ${data.shapes.length} boxes, ${data.svgShapes.length} paths, ${data.icons.length} icons, ${particles.length} particles`);
    await p.close();
  }
  await b.close();
})().catch(e => { console.error('ERR', e); process.exit(1); });
