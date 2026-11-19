/* SPDX-License-Identifier: MIT */
/* demo-engine: slides, modes, staff panel, idle return, wall loop, slide picker, report viewer, terminal slot.
 * Reads window.DEMO_CONFIG (defaults) and the URL (wins over the defaults). Vanilla JS, no dependencies.
 *
 * URL options: ?mode=staffed|presenter|kiosk|wall  ?playlist=KEY  ?speed=N  ?theme=light|dark  ?lock  ?idle=SECONDS
 *              ?admin (open the staff panel)  ?reset (forget the unlocked staff session)  #N (open slide N)
 * Keys:        → ← Space PgUp PgDn, 1-9, Home, End, G picker, L theme, F full screen, P pause the loop, Esc close,
 *              the staff chord from CONFIG (default Ctrl+Alt+S) opens the staff panel in every mode.
 */
(function () {
  'use strict';
  var C = window.DEMO_CONFIG || {};
  var q = new URLSearchParams(location.search);
  var MODES = ['staffed', 'presenter', 'kiosk', 'wall'];
  var mode = MODES.indexOf(q.get('mode')) >= 0 ? q.get('mode') : (MODES.indexOf(C.mode) >= 0 ? C.mode : 'staffed');
  var speed = clamp(parseFloat(q.get('speed')) || C.speed || 1, 0.25, 8);
  var idleS = q.has('idle') ? Math.max(0, parseInt(q.get('idle'), 10) || 0) : (C.idleSeconds == null ? 90 : C.idleSeconds);
  var locked = q.has('lock') || mode === 'kiosk' || mode === 'wall';
  var playlists = C.playlists || {};
  var plKey = playlists[q.get('playlist')] ? q.get('playlist') : (C.playlist || 'all');
  var reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  var root = document.documentElement;
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }
  function within(e, sel) { return !!(e.target && e.target.closest && e.target.closest(sel)); }

  if (q.has('reset')) { try { sessionStorage.removeItem('demo-staff'); localStorage.removeItem('demo-theme'); } catch (e) {} }
  root.dataset.mode = mode;

  /* ---------- theme ---------- */
  function setTheme(t, save) { root.setAttribute('data-theme', t === 'light' ? 'light' : 'dark'); if (save) { try { localStorage.setItem('demo-theme', t); } catch (e) {} } }
  function toggleTheme() { setTheme(root.getAttribute('data-theme') === 'light' ? 'dark' : 'light', true); }

  /* ---------- stage fit ---------- */
  var stage = $('#stage'), viewport = $('#viewport');
  function fit() { var s = Math.min(viewport.clientWidth / 1920, viewport.clientHeight / 1080); stage.style.transform = 'scale(' + s + ') translate(-50%,-50%)'; }
  addEventListener('resize', fit); fit();

  /* ---------- slides ---------- */
  var slides = $$('.slide'), N = slides.length, cur = -1;
  var order = (playlists[plKey] || slides.map(function (_, i) { return i + 1; })).map(function (n) { return n - 1; }).filter(function (i) { return i >= 0 && i < N; });
  var counter = $('#counter'), progress = $('#progress');
  function title(i) { return slides[i].dataset.title || slides[i].getAttribute('aria-label') || ('Slide ' + (i + 1)); }
  function go(i, from) {
    i = clamp(i, 0, N - 1);
    if (i === cur) return;
    slides.forEach(function (s, k) { s.classList.toggle('on', k === i); s.classList.toggle('left', k < i); s.setAttribute('aria-hidden', k !== i); s.inert = k !== i; });
    cur = i;
    counter.textContent = (i + 1) + ' / ' + N;
    progress.style.transform = 'scaleX(' + ((i + 1) / N) + ')';
    try { history.replaceState(null, '', location.pathname + location.search + '#' + (i + 1)); }
    catch (e) { location.hash = '#' + (i + 1); }       // some file:// contexts refuse replaceState
    $('#live').textContent = 'Slide ' + (i + 1) + ' of ' + N + ': ' + title(i);
    onEnter(slides[i]);
    if (mode === 'wall' && from !== 'loop') scheduleLoop();
  }
  function next() { go(cur + 1); }
  function prev() { go(cur - 1); }

  /* ---------- terminal slot and report button, per slide ---------- */
  var term = null;
  function onEnter(s) {
    var slot = $('.term-slot', s);
    if (term) { term.destroy(); term = null; }
    if (slot && window.TermPlayer && window.DEMO_SESSION) {
      var host = document.createElement('div'); slot.innerHTML = ''; slot.appendChild(host);
      term = TermPlayer.mount(host, window.DEMO_SESSION, { speed: speed, autoplay: mode === 'wall', reducedMotion: reduce });
    }
  }
  function slideDwell(i) {
    var s = slides[i], d = parseFloat(s.dataset.dwell) || C.dwellSeconds || 9;
    if ($('.term-slot', s) && window.TermPlayer && window.DEMO_SESSION) {
      var ms = TermPlayer.timing(window.DEMO_SESSION, speed).reduce(function (a, r) { return a + r.ms; }, 0);
      d = Math.max(d, ms / 1000 + 3);
    }
    return d * 1000 / (s.querySelector('.term-slot') ? 1 : speed);
  }

  /* ---------- wall loop: fixed first item, then the playlist in order ---------- */
  var loopT = null, loopPaused = false, loopIdx = 0;
  function scheduleLoop() {
    clearTimeout(loopT);
    if (mode !== 'wall' || loopPaused) return;
    loopT = setTimeout(function () { loopIdx = (loopIdx + 1) % order.length; go(order[loopIdx], 'loop'); scheduleLoop(); }, slideDwell(cur));
  }
  function setLoopPaused(p) {
    loopPaused = p;
    var b = $('#pausebtn'); if (b) { b.setAttribute('aria-pressed', p); b.querySelector('span').textContent = p ? 'Play' : 'Pause'; }
    if (term) p ? term.pause() : term.play();
    if (!p) scheduleLoop(); else clearTimeout(loopT);
  }

  /* ---------- idle return (staffed and kiosk; never while presenting) ---------- */
  var lastInput = Date.now();
  function touch() { lastInput = Date.now(); }
  setInterval(function () {
    if (!idleS || mode === 'presenter' || Date.now() - lastInput < idleS * 1000) return;
    if (mode === 'wall') { if (loopPaused) setLoopPaused(false); return; }   // a paused loop resumes on its own
    if (cur !== order[0] || (term && term.scene() !== (window.DEMO_SESSION || {}).start)) { closeAll(); cur = -1; go(order[0]); }
    lastInput = Date.now();
  }, 1000);

  /* ---------- overlays ---------- */
  var openOverlay = null, lastFocus = null;
  function open(id) {
    closeAll(); var o = document.getElementById(id); if (!o) return;
    lastFocus = document.activeElement; o.classList.add('open'); openOverlay = o;
    var f = o.querySelector('[autofocus],button,input,[tabindex="0"]'); if (f) f.focus();
  }
  function closeAll() { $$('.overlay.open').forEach(function (o) { o.classList.remove('open'); }); if (openOverlay && lastFocus) lastFocus.focus(); openOverlay = null; }
  $$('[data-close]').forEach(function (b) { b.addEventListener('click', closeAll); });
  $$('.overlay').forEach(function (o) { o.addEventListener('click', function (e) { if (e.target === o) closeAll(); }); });
  // keep Tab inside an open dialog
  addEventListener('keydown', function (e) {
    if (e.key !== 'Tab' || !openOverlay) return;
    var f = $$('button,input,select,[tabindex="0"]', openOverlay).filter(function (x) { return !x.disabled && x.offsetParent !== null; });
    if (!f.length) return;
    if (e.shiftKey && document.activeElement === f[0]) { e.preventDefault(); f[f.length - 1].focus(); }
    else if (!e.shiftKey && document.activeElement === f[f.length - 1]) { e.preventDefault(); f[0].focus(); }
  });

  /* ---------- slide picker (G or the grid button; hidden in kiosk and wall) ---------- */
  function openPicker() {
    if (mode === 'kiosk' || mode === 'wall') return;
    var g = $('#picker-grid'); g.innerHTML = '';
    slides.forEach(function (s, i) {
      var b = document.createElement('button'); b.type = 'button';
      b.innerHTML = '<b>' + (i + 1) + '</b>' + escapeHtml(title(i));
      if (i === cur) b.setAttribute('aria-current', 'true');
      b.addEventListener('click', function () { closeAll(); go(i); });
      g.appendChild(b);
    });
    open('picker');
  }
  function escapeHtml(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }

  /* ---------- staff panel: a convenience gate for a booth, NOT security ---------- */
  function unlocked() { try { return sessionStorage.getItem('demo-staff') === C.staffCodeSha256; } catch (e) { return false; } }
  function openStaff() {
    if (unlocked()) return showStaffBody();
    $('#staff-gate').hidden = false; $('#staff-body').hidden = true; $('#staff-msg').textContent = '';
    $('#staff-code').value = ''; open('staff'); $('#staff-code').focus();
  }
  function tryCode() {
    var v = $('#staff-code').value.trim();
    if (sha256(v) === C.staffCodeSha256) { try { sessionStorage.setItem('demo-staff', C.staffCodeSha256); } catch (e) {} showStaffBody(); }
    else { $('#staff-msg').textContent = 'That code did not match.'; $('#staff-code').select(); }
  }
  function showStaffBody() {
    $('#staff-gate').hidden = true; $('#staff-body').hidden = false;
    $$('[data-setmode]').forEach(function (b) { b.setAttribute('aria-pressed', b.dataset.setmode === mode); });
    var pl = $('#staff-playlist'); pl.innerHTML = '';
    Object.keys(playlists).forEach(function (k) { var o = document.createElement('option'); o.value = k; o.textContent = k + ' (' + playlists[k].length + ' slides)'; if (k === plKey) o.selected = true; pl.appendChild(o); });
    var j = $('#staff-jump'); j.innerHTML = '';
    slides.forEach(function (s, i) { var b = document.createElement('button'); b.type = 'button'; b.className = 'btn'; b.textContent = (i + 1) + ' · ' + title(i); b.addEventListener('click', function () { closeAll(); go(i); }); j.appendChild(b); });
    if (!openOverlay) open('staff');
    var f = $('#staff-body button'); if (f) f.focus();
  }
  function relaunch(params) {
    var p = new URLSearchParams(location.search);
    ['admin', 'reset'].forEach(function (k) { p.delete(k); });
    Object.keys(params).forEach(function (k) { params[k] == null ? p.delete(k) : p.set(k, params[k]); });
    location.search = p.toString();
  }
  $('#staff-ok').addEventListener('click', tryCode);
  $('#staff-code').addEventListener('keydown', function (e) { if (e.key === 'Enter') tryCode(); });
  $$('[data-setmode]').forEach(function (b) { b.addEventListener('click', function () { relaunch({ mode: b.dataset.setmode, playlist: $('#staff-playlist').value }); }); });
  $('#staff-idle').addEventListener('click', function () { lastInput = Date.now(); $('#staff-note').textContent = 'Idle timer reset.'; });
  $('#staff-restart').addEventListener('click', function () { closeAll(); cur = -1; loopIdx = 0; go(order[0]); });
  $('#staff-theme').addEventListener('click', toggleTheme);
  $('#staff-lock').addEventListener('click', function () { try { sessionStorage.removeItem('demo-staff'); } catch (e) {} closeAll(); });

  /* ---------- report viewer: Human and Machine tabs, zoom, Esc closes ---------- */
  var zoom = 1;
  function setZoom(z) { zoom = clamp(z, 0.5, 3); $$('.zoomable').forEach(function (el) { el.style.transform = 'scale(' + zoom + ')'; el.style.width = (100 / zoom) + '%'; }); $('#zoom-val').textContent = Math.round(zoom * 100) + '%'; }
  function renderReport() {
    var r = window.DEMO_REPORT || {};
    var h = '<h2 style="margin:0 0 6px">' + escapeHtml(r.title || 'Report') + '</h2><p>' + escapeHtml(r.summary || '') + '</p>';
    (r.sections || []).forEach(function (sec) {
      h += '<h3>' + escapeHtml(sec.title) + '</h3>';
      if (sec.rows) {
        h += '<table><thead><tr>' + sec.columns.map(function (c) { return '<th>' + escapeHtml(c) + '</th>'; }).join('') + '</tr></thead><tbody>';
        sec.rows.forEach(function (row) { h += '<tr>' + row.map(function (c) { var m = /^(ok|warn|err):(.*)$/.exec(String(c)); return m ? '<td class="' + m[1] + '">' + escapeHtml(m[2]) + '</td>' : '<td>' + escapeHtml(c) + '</td>'; }).join('') + '</tr>'; });
        h += '</tbody></table>';
      }
      if (sec.text) h += '<p>' + escapeHtml(sec.text) + '</p>';
    });
    $('#report-human').innerHTML = h;
    $('#report-json').textContent = JSON.stringify(r, null, 2);
  }
  function tab(which) {
    $$('#report [role="tab"]').forEach(function (t) { var on = t.dataset.tab === which; t.setAttribute('aria-selected', on); t.tabIndex = on ? 0 : -1; });
    $('#panel-human').hidden = which !== 'human'; $('#panel-json').hidden = which !== 'json';
  }
  function openReport() { renderReport(); tab('human'); setZoom(1); open('report'); }
  $$('#report [role="tab"]').forEach(function (t) {
    t.addEventListener('click', function () { tab(t.dataset.tab); });
    t.addEventListener('keydown', function (e) { if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') { e.preventDefault(); e.stopPropagation(); var o = t.dataset.tab === 'human' ? 'json' : 'human'; tab(o); $('#report [data-tab="' + o + '"]').focus(); } });
  });
  $('#zoom-in').addEventListener('click', function () { setZoom(zoom + 0.1); });
  $('#zoom-out').addEventListener('click', function () { setZoom(zoom - 0.1); });
  $('#zoom-reset').addEventListener('click', function () { setZoom(1); });
  $$('#report .viewer').forEach(function (v) {
    v.addEventListener('wheel', function (e) { if (e.ctrlKey) { e.preventDefault(); setZoom(zoom * (e.deltaY < 0 ? 1.08 : 1 / 1.08)); } }, { passive: false });
    var pts = {}, startD = 0, startZ = 1;
    function dist() { var p = Object.keys(pts).map(function (k) { return pts[k]; }); return p.length < 2 ? 0 : Math.hypot(p[0].x - p[1].x, p[0].y - p[1].y); }
    v.addEventListener('pointerdown', function (e) { pts[e.pointerId] = { x: e.clientX, y: e.clientY }; if (Object.keys(pts).length === 2) { startD = dist(); startZ = zoom; } });
    v.addEventListener('pointermove', function (e) { if (!pts[e.pointerId]) return; pts[e.pointerId] = { x: e.clientX, y: e.clientY }; if (Object.keys(pts).length === 2 && startD) setZoom(startZ * dist() / startD); });
    ['pointerup', 'pointercancel', 'pointerleave'].forEach(function (t) { v.addEventListener(t, function (e) { delete pts[e.pointerId]; if (Object.keys(pts).length < 2) startD = 0; }); });
  });
  $$('[data-open-report]').forEach(function (b) { b.addEventListener('click', openReport); });

  /* ---------- input ---------- */
  function chord(e) { var k = C.chord || { key: 'S', ctrl: true, alt: true }; return e.key.toUpperCase() === k.key && !!e.ctrlKey === !!k.ctrl && !!e.altKey === !!k.alt && !!e.shiftKey === !!k.shift; }
  addEventListener('keydown', function (e) {
    touch();
    if (chord(e)) { e.preventDefault(); openStaff(); return; }
    if (e.key === 'Escape') { closeAll(); return; }
    if (openOverlay || within(e, 'input,select,textarea')) return;
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    var k = e.key;
    if (k === 'p' || k === 'P') { if (mode === 'wall') setLoopPaused(!loopPaused); else if (term) term.toggle(); return; }
    if (mode === 'wall') return;                               // the loop ignores everything else
    if (k === 'ArrowRight' || k === 'PageDown' || (k === ' ' && !within(e, 'button,.tp-screen'))) { e.preventDefault(); next(); }
    else if (k === 'ArrowLeft' || k === 'PageUp') { e.preventDefault(); prev(); }
    else if (k === 'Home') go(0);
    else if (k === 'End') go(N - 1);
    else if (/^[1-9]$/.test(k) && +k <= N) go(+k - 1);
    else if ((k === 'g' || k === 'G')) openPicker();
    else if ((k === 'l' || k === 'L') && !locked) toggleTheme();
    else if (k === 'f' || k === 'F') { if (!document.fullscreenElement) root.requestFullscreen && root.requestFullscreen(); else document.exitFullscreen && document.exitFullscreen(); }
  });
  ['pointerdown', 'wheel', 'touchstart'].forEach(function (t) { addEventListener(t, touch, { passive: true }); });
  var tx = null;
  addEventListener('touchstart', function (e) { tx = e.changedTouches[0].clientX; }, { passive: true });
  addEventListener('touchend', function (e) { if (tx === null || mode === 'wall' || openOverlay) return; var dx = e.changedTouches[0].clientX - tx; if (Math.abs(dx) > 60) (dx < 0 ? next : prev)(); tx = null; }, { passive: true });
  stage.addEventListener('click', function (e) { if (mode === 'wall' || mode === 'kiosk' || within(e, 'button,a,input,select,.tp,[data-no-advance]')) return; next(); });
  $('#prev').addEventListener('click', prev);
  $('#next').addEventListener('click', next);
  $('#gridbtn').addEventListener('click', openPicker);
  $('#themebtn').addEventListener('click', toggleTheme);
  $('#gearbtn').addEventListener('click', openStaff);
  $('#pausebtn').addEventListener('click', function () { setLoopPaused(!loopPaused); });
  addEventListener('hashchange', function () { var n = parseInt(location.hash.slice(1), 10); if (n && n - 1 !== cur && mode !== 'wall') go(n - 1); });

  /* ---------- start ---------- */
  $('#modetag').textContent = mode + (locked && mode !== 'kiosk' && mode !== 'wall' ? ' · locked' : '');
  if (mode !== 'wall') $('#pausebtn').hidden = true;
  if (locked) { $('#themebtn').hidden = true; $('#gearbtn').hidden = true; $('#gridbtn').hidden = mode !== 'staffed' && mode !== 'presenter'; }
  setTimeout(function () { var h = $('#hint'); if (h) h.classList.add('gone'); }, 6000);
  var startAt = parseInt(location.hash.slice(1), 10);
  if (mode === 'wall') { loopIdx = 0; go(order[0]); }                      // always the first item, never a random one
  else go(startAt ? startAt - 1 : order[0]);
  if (q.has('admin')) openStaff();

  /* ---------- SHA-256 (FIPS 180-4), so the staff check works from file:// in any browser ---------- */
  function sha256(str) {
    var K = [], H = [], i, j, isP = function (n) { for (var d = 2; d * d <= n; d++) if (n % d === 0) return false; return true; };
    for (var n = 2, c = 0; c < 64; n++) if (isP(n)) { if (c < 8) H[c] = (Math.pow(n, 1 / 2) * 4294967296) | 0; K[c++] = (Math.pow(n, 1 / 3) * 4294967296) | 0; }
    var bytes = unescape(encodeURIComponent(str)), l = bytes.length, words = [];
    for (i = 0; i < l; i++) words[i >> 2] |= bytes.charCodeAt(i) << (24 - (i % 4) * 8);
    words[l >> 2] |= 0x80 << (24 - (l % 4) * 8);
    words[(((l + 8) >> 6) << 4) + 15] = l * 8;
    var r = function (x, k) { return (x >>> k) | (x << (32 - k)); };
    for (j = 0; j < words.length; j += 16) {
      for (var w = [], x = 0; x < 16; x++) w[x] = words[j + x] | 0;   // the padded block has holes; fill them with 0
      var a = H.slice(0);
      for (i = 0; i < 64; i++) {
        if (i >= 16) { var w15 = w[i - 15], w2 = w[i - 2]; w[i] = (w[i - 16] + (r(w15, 7) ^ r(w15, 18) ^ (w15 >>> 3)) + w[i - 7] + (r(w2, 17) ^ r(w2, 19) ^ (w2 >>> 10))) | 0; }
        var t1 = (a[7] + (r(a[4], 6) ^ r(a[4], 11) ^ r(a[4], 25)) + ((a[4] & a[5]) ^ (~a[4] & a[6])) + K[i] + (w[i] | 0)) | 0;
        var t2 = ((r(a[0], 2) ^ r(a[0], 13) ^ r(a[0], 22)) + ((a[0] & a[1]) ^ (a[0] & a[2]) ^ (a[1] & a[2]))) | 0;
        a = [(t1 + t2) | 0].concat(a.slice(0, 7)); a[4] = (a[4] + t1) | 0;
      }
      for (i = 0; i < 8; i++) H[i] = (H[i] + a[i]) | 0;
    }
    return H.map(function (h) { return ('00000000' + (h >>> 0).toString(16)).slice(-8); }).join('');
  }
  window.DemoEngine = { go: go, next: next, prev: prev, openReport: openReport, openStaff: openStaff, sha256: sha256 };
})();
