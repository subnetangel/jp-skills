/* SPDX-License-Identifier: MIT */
/* term-player.js: plays a recreated terminal session from a session script (see references/session-format.md).
 * Vanilla JS, no dependencies. One function of the script and the clock: the same script gives the same screen.
 *
 *   const p = TermPlayer.mount(el, session, { speed: 1, autoplay: true, reducedMotion: false,
 *                                            onScene: id => {}, onEnd: () => {} });
 *   p.play(); p.pause(); p.toggle(); p.restart(); p.goto('scene-id'); p.setStep(true); p.next(); p.destroy();
 *   TermPlayer.timing(session, speed)  -> [{id, stage, ms}]  (the main path, same formula as build_replay.py)
 */
(function (global) {
  'use strict';
  var STOP = {};
  var TAG = /\[\[(ok|warn|err|dim|em|cmd):([^\]]*)\]\]/g;

  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; });
  }
  function markup(s) { return esc(s).replace(TAG, '<span class="tp-$1">$2</span>'); }
  function plain(s) { return String(s).replace(TAG, '$2'); }
  function el(tag, cls, html) { var e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; }

  /* Timing model, shared with scripts/build_replay.py: typing chars/cps + enter, one line every line_ms, pauses as
     written, then the scene's hold before an automatic choice. Everything divides by speed. */
  function eventMs(ev, t) {
    if (ev.type === 'type') return plain(ev.text).length / t.type_cps * 1000 + t.enter_ms;
    if (ev.type === 'out') return (ev.lines || []).length * (ev.line_ms || t.line_ms);
    if (ev.type === 'note') return t.line_ms;
    if (ev.type === 'pause') return ev.ms || 0;
    return 0;
  }
  function tune(session) {
    var t = session.timing || {};
    return { type_cps: t.type_cps || 40, enter_ms: t.enter_ms == null ? 250 : t.enter_ms,
             line_ms: t.line_ms || 70, hold_ms: t.hold_ms == null ? 1800 : t.hold_ms };
  }
  function scenes(session) { var m = {}; (session.scenes || []).forEach(function (s) { m[s.id] = s; }); return m; }
  function autoNext(s) {
    if (s.auto) return s.auto;
    if (s.choices && s.choices.length) return s.choices[0].goto;
    return s.next || null;
  }
  function timing(session, speed) {
    var t = tune(session), m = scenes(session), out = [], seen = {}, id = session.start || (session.scenes[0] || {}).id;
    while (id && m[id] && !seen[id]) {
      seen[id] = 1;
      var s = m[id], ms = (s.events || []).reduce(function (a, e) { return a + eventMs(e, t); }, 0);
      if (s.choices && s.choices.length) ms += t.hold_ms;
      out.push({ id: id, stage: s.stage || '', ms: ms / (speed || 1) });
      id = autoNext(s);
    }
    return out;
  }

  function mount(root, session, opts) {
    opts = opts || {};
    var t = tune(session), m = scenes(session);
    var st = { speed: +opts.speed > 0 ? +opts.speed : 1, autoplay: opts.autoplay !== false, paused: false, step: false,
               tok: 0, waiter: null, scene: null, reduce: !!opts.reducedMotion };
    root.classList.add('tp');
    root.innerHTML = '';
    var bar = el('div', 'tp-bar');
    var badge = el('span', 'tp-badge', esc(session.badge || 'Recreated, not live'));
    badge.title = session.label || 'A scripted recreation of a session. Nothing here runs live.';
    var stage = el('span', 'tp-stage'), title = el('span', 'tp-title', esc(session.title || ''));
    var ctl = el('span', 'tp-ctl');
    function btn(label, aria, fn) { var b = el('button', 'tp-btn', label); b.type = 'button'; b.setAttribute('aria-label', aria); b.addEventListener('click', fn); ctl.appendChild(b); return b; }
    var bPlay = btn('Pause', 'Pause or play the replay', function () { api.toggle(); });
    btn('Restart', 'Restart the replay from the beginning', function () { api.restart(); });
    var bStep = btn('Step: off', 'Step through one line at a time', function () { api.setStep(!st.step); });
    var bNext = btn('Next', 'Show the next line', function () { api.next(); });
    bNext.hidden = true;
    bar.append(badge, stage, title, ctl);
    var screen = el('div', 'tp-screen');
    screen.setAttribute('role', 'log'); screen.setAttribute('aria-label', session.aria || 'Recreated terminal session');
    screen.tabIndex = 0;
    var lines = el('div', 'tp-lines');
    screen.appendChild(lines);
    var caption = el('div', 'tp-caption'); caption.setAttribute('aria-live', 'polite');
    var chips = el('div', 'tp-chips'); chips.setAttribute('role', 'group'); chips.setAttribute('aria-label', 'Choices');
    root.append(bar, screen, caption, chips);

    function stick() { screen.scrollTop = screen.scrollHeight; }
    function line(html, cls) { var d = el('div', 'tp-line' + (cls ? ' ' + cls : ''), html); lines.appendChild(d); stick(); return d; }
    function alive(tok) { if (tok !== st.tok) throw STOP; }
    function wait(ms, tok) {
      var left = ms / st.speed;
      return new Promise(function (res, rej) {
        (function tick() {
          if (tok !== st.tok) return rej(STOP);
          if (left <= 0) return res();
          var d = Math.min(40, left);
          setTimeout(function () { if (!st.paused) left -= d; tick(); }, d);
        })();
      });
    }
    function stepGate(tok) {
      if (!st.step) return Promise.resolve();
      return new Promise(function (res, rej) { st.waiter = function () { st.waiter = null; tok === st.tok ? res() : rej(STOP); }; });
    }
    function setPaused(p) { st.paused = p; bPlay.textContent = p ? 'Play' : 'Pause'; root.classList.toggle('tp-paused', p); }

    async function typeLine(ev, tok) {
      var d = line('<span class="tp-prompt">' + esc(ev.prompt != null ? ev.prompt : (session.prompt || '$ ')) + '</span><span class="tp-typed"></span><span class="tp-cursor" aria-hidden="true"></span>');
      var typed = d.querySelector('.tp-typed'), text = plain(ev.text);
      if (st.reduce) { typed.textContent = text; await wait(t.enter_ms, tok); }
      else {
        var per = 1000 / t.type_cps;
        for (var i = 1; i <= text.length; i++) { typed.textContent = text.slice(0, i); await wait(per, tok); }
        await wait(t.enter_ms, tok);
      }
      typed.innerHTML = markup(ev.text);
      var c = d.querySelector('.tp-cursor'); if (c) c.remove();
    }
    async function run(ev, tok) {
      alive(tok);
      if (ev.type === 'type') await typeLine(ev, tok);
      else if (ev.type === 'out') {
        for (var i = 0; i < (ev.lines || []).length; i++) { line(markup(ev.lines[i]), ev.cls ? 'tp-' + ev.cls : ''); await wait(ev.line_ms || t.line_ms, tok); }
      }
      else if (ev.type === 'note') { line('<span class="tp-note-mark" aria-hidden="true">›</span> ' + markup(ev.text), 'tp-note'); await wait(t.line_ms, tok); }
      else if (ev.type === 'pause') await wait(ev.ms || 0, tok);
      else if (ev.type === 'caption') caption.innerHTML = markup(ev.text || '');
      else if (ev.type === 'stage') stage.textContent = ev.text || '';
      else if (ev.type === 'clear') lines.innerHTML = '';
      await stepGate(tok);
    }
    function showChips(s, tok) {
      chips.innerHTML = '';
      (s.choices || []).forEach(function (c) {
        var b = el('button', 'tp-chip tp-chip-' + (c.kind || 'next'), esc(c.label)); b.type = 'button';
        b.addEventListener('click', function () { api.goto(c.goto); });
        chips.appendChild(b);
      });
      if (st.autoplay && (s.choices || []).length) {
        wait(t.hold_ms, tok).then(function () { api.goto(autoNext(s)); }, function () {});
      }
    }
    async function playScene(id) {
      var tok = ++st.tok, s = m[id];
      chips.innerHTML = '';
      if (!s) return;
      st.scene = id;
      root.dataset.scene = id;
      if (s.clear) lines.innerHTML = '';
      stage.textContent = s.stage || '';
      caption.innerHTML = markup(s.caption || '');
      if (opts.onScene) opts.onScene(id, s);
      try {
        for (var i = 0; i < (s.events || []).length; i++) await run(s.events[i], tok);
        if (s.choices && s.choices.length) showChips(s, tok);
        else if (s.next) { await wait(t.hold_ms / 2, tok); api.goto(s.next); }
        else { root.classList.add('tp-ended'); if (opts.onEnd) opts.onEnd(); }
      } catch (e) { if (e !== STOP) throw e; }
    }
    var api = {
      play: function () { setPaused(false); },
      pause: function () { setPaused(true); },
      toggle: function () { setPaused(!st.paused); },
      restart: function () { root.classList.remove('tp-ended'); lines.innerHTML = ''; setPaused(false); playScene(session.start || session.scenes[0].id); },
      goto: function (id) { if (id) { root.classList.remove('tp-ended'); playScene(id); } },
      setStep: function (on) { st.step = !!on; bStep.textContent = 'Step: ' + (on ? 'on' : 'off'); bNext.hidden = !on; if (!on && st.waiter) st.waiter(); },
      next: function () { if (st.waiter) st.waiter(); },
      setSpeed: function (s) { if (+s > 0) st.speed = +s; },
      setAutoplay: function (a) { st.autoplay = !!a; },
      scene: function () { return st.scene; },
      destroy: function () { st.tok++; root.innerHTML = ''; }
    };
    screen.addEventListener('keydown', function (e) {
      if (e.key === ' ' || e.key === 'Enter') { e.preventDefault(); e.stopPropagation(); st.step ? api.next() : api.toggle(); }
    });
    if (opts.start !== false) api.restart();
    return api;
  }

  global.TermPlayer = { mount: mount, timing: timing, plain: plain };
})(window);
