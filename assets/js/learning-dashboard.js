/* Enhance native details; without JS the complete dashboard remains readable. */
(() => {
  const root = document.querySelector('[data-learning-dashboard]');
  if (!root) return;
  const motion = matchMedia('(prefers-reduced-motion: reduce)');
  const duration = 320;
  const controllers = new Map();

  root.querySelectorAll('details').forEach(details => {
    const summary = details.querySelector(':scope > summary');
    if (!summary) return;
    const body = document.createElement('div');
    const inner = document.createElement('div');
    body.className = 'journey-disclosure-body';
    inner.className = 'journey-disclosure-inner';
    // One measured body includes lists and their margins, including nested details.
    [...details.childNodes].filter(node => node !== summary).forEach(node => inner.append(node));
    body.append(inner);
    details.append(body);
    details.dataset.disclosureReady = '';
    let expanded = details.open;
    let timer = 0;
    let running = false;
    const preview = summary.querySelector('.journey-task-preview');

    function measurePreview() {
      if (preview) preview.style.setProperty('--preview-height', preview.scrollHeight + 'px');
    }
    function finish() {
      clearTimeout(timer);
      running = false;
      body.style.transition = 'none';
      body.style.height = expanded ? 'auto' : '0px';
      details.open = expanded;
      body.inert = !expanded;
      delete details.dataset.disclosureAnimating;
    }
    function setOpen(next, animate = true) {
      // Read the current rendered height before reversing an unfinished animation.
      const start = body.getBoundingClientRect().height;
      clearTimeout(timer);
      body.style.transition = 'none';
      body.style.height = start + 'px';
      expanded = next;
      details.open = true; // Keep content rendered until a closing transition ends.
      measurePreview();
      details.dataset.expanded = String(expanded);
      summary.setAttribute('aria-expanded', String(expanded));
      body.inert = !expanded;
      const end = expanded ? inner.getBoundingClientRect().height : 0;
      if (!animate || motion.matches || Math.abs(end - start) < 1) {
        finish();
        return;
      }
      running = true;
      details.dataset.disclosureAnimating = '';
      // Commit the current frame; the following height uses the CSS transition.
      void body.offsetHeight;
      body.style.removeProperty('transition');
      body.style.height = end + 'px';
      timer = setTimeout(finish, duration + 80);
    }

    details.dataset.expanded = String(expanded);
    summary.setAttribute('aria-expanded', String(expanded));
    measurePreview();
    finish();
    summary.addEventListener('click', event => {
      if (event.target.closest('a,button,input,select,textarea')) return;
      event.preventDefault(); // Enter/Space activate native summary via click too.
      setOpen(!expanded);
    });
    body.addEventListener('transitionend', event => {
      if (event.target === body && event.propertyName === 'height') finish();
    });
    details.addEventListener('toggle', () => {
      // Browser find-in-page or an external native open change must stay in sync.
      if (!running && details.open !== expanded) setOpen(details.open, false);
    });
    if ('ResizeObserver' in window) {
      new ResizeObserver(() => {
        if (!running || !expanded) return;
        const height = inner.getBoundingClientRect().height;
        if (Math.abs(height - parseFloat(body.style.height)) < 1) return;
        body.style.height = height + 'px';
        clearTimeout(timer);
        timer = setTimeout(finish, duration + 80);
      }).observe(inner);
    }
    controllers.set(details, {setOpen, finish, measurePreview});
  });

  // Drop fixed heights on viewport changes or when reduced motion is enabled.
  window.addEventListener('resize', () => controllers.forEach(c => {
    c.finish();
    c.measurePreview();
  }), {passive: true});
  motion.addEventListener('change', () => controllers.forEach(c => c.finish()));

  function revealTarget() {
    let id;
    try { id = decodeURIComponent(location.hash.slice(1)); } catch { return; }
    const target = document.getElementById(id);
    if (!target || !root.contains(target)) return;
    const detail = target.querySelector(':scope > details');
    if (detail) controllers.get(detail)?.setOpen(true, false);
    let node = target;
    // Direct task links should land at readable content, without delayed scrolling.
    while (node && node !== root) {
      if (node.tagName === 'DETAILS') controllers.get(node)?.setOpen(true, false);
      node = node.parentElement;
    }
    requestAnimationFrame(() => target.scrollIntoView({block: 'start'}));
  }
  root.addEventListener('click', event => {
    const link = event.target.closest('a[href^="#"]');
    if (link && link.hash === location.hash) revealTarget();
  });
  window.addEventListener('hashchange', revealTarget);
  revealTarget();
})();
