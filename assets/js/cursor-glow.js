/* Pointer-driven only: one queued frame per movement, no idle animation loop. */
(() => {
  const root = document.documentElement;
  const mouse = matchMedia('(hover: hover) and (pointer: fine)');
  const quiet = matchMedia('(prefers-reduced-motion: reduce), (prefers-reduced-transparency: reduce), (prefers-contrast: more), (forced-colors: active)');
  const glow = document.createElement('div');
  glow.className = 'cursor-glow';
  glow.setAttribute('aria-hidden', 'true');
  const spot = document.createElement('div');
  spot.className = 'cursor-glow__spot';
  glow.append(spot);
  document.body.append(glow);

  let enabled = false, frame = 0, point = null;
  function hide() {
    cancelAnimationFrame(frame);
    frame = 0;
    point = null;
    glow.classList.remove('is-active');
  }
  function paint() {
    frame = 0;
    if (!enabled || !point) return;
    spot.style.transform = `translate3d(${point.x}px,${point.y}px,0) translate(-50%,-50%)`;
    glow.classList.add('is-active');
  }
  function move(event) {
    if (event.pointerType !== 'mouse') { hide(); return; }
    point = {x:event.clientX, y:event.clientY};
    if (!frame) frame = requestAnimationFrame(paint);
  }
  function sync() {
    const next = root.dataset.theme === 'dark' && mouse.matches && !quiet.matches && !document.hidden;
    if (next === enabled) return;
    enabled = next;
    if (enabled) document.addEventListener('pointermove', move, {passive:true});
    else {
      document.removeEventListener('pointermove', move);
      hide();
    }
  }

  // Theme changes may also come from restored browser state, not just the button.
  new MutationObserver(sync).observe(root, {attributes:true, attributeFilter:['data-theme']});
  mouse.addEventListener('change', sync);
  quiet.addEventListener('change', sync);
  document.addEventListener('visibilitychange', sync);
  document.addEventListener('pointerout', event => { if (!event.relatedTarget) hide(); }, {passive:true});
  document.addEventListener('pointercancel', hide, {passive:true});
  addEventListener('blur', hide);
  addEventListener('resize', hide, {passive:true});
  addEventListener('pagehide', hide);
  addEventListener('pageshow', sync);
  sync();
})();
