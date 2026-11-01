/* A native sun/moon button with an optional radial view transition. */
(() => {
  const button = document.getElementById('theme');
  if (!button) return;
  const root = document.documentElement;
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  let intendedDark = root.dataset.theme === 'dark';
  let generation = 0, transition = null, reveal = null;

  function applyTheme(dark, save = true) {
    root.dataset.theme = dark ? 'dark' : 'light';
    root.style.colorScheme = root.dataset.theme;
    document.body.classList.remove('light', 'dark');
    document.body.classList.add(root.dataset.theme);
    const label = dark ? '切换到日间模式' : '切换到夜间模式';
    button.setAttribute('aria-label', label);
    button.setAttribute('aria-pressed', String(dark));
    button.title = label;
    if (save) { try { localStorage.setItem('wish-typo-theme', root.dataset.theme); } catch {} }
  }
  applyTheme(intendedDark, false);

  function toggleTheme() {
    intendedDark = !intendedDark;
    const next = intendedDark, token = ++generation;
    reveal?.cancel();
    transition?.skipTransition();
    if (reduced.matches || typeof document.startViewTransition !== 'function') {
      applyTheme(next);
      return;
    }
    const box = button.getBoundingClientRect();
    const x = box.left + box.width / 2, y = box.top + box.height / 2;
    const radius = Math.hypot(Math.max(x, innerWidth-x), Math.max(y, innerHeight-y)) + 4;
    let active;
    try {
      active = document.startViewTransition(() => {
        if (token === generation) applyTheme(next);
      });
    } catch {
      applyTheme(next);
      return;
    }
    transition = active;
    active.ready.then(() => {
      if (token !== generation || reduced.matches) { active.skipTransition(); return; }
      try {
        reveal = root.animate({clipPath:[`circle(0px at ${x}px ${y}px)`,`circle(${radius}px at ${x}px ${y}px)`]}, {
          duration:680,easing:'cubic-bezier(.65,0,.35,1)',pseudoElement:'::view-transition-new(root)'
        });
        reveal.finished.catch(() => {});
      } catch { active.skipTransition(); }
    }).catch(() => {});
    active.finished.then(() => {
      if (transition === active) { transition = null; reveal = null; }
    }, () => {});
  }
  button.addEventListener('click', toggleTheme);

  function settle() {
    ++generation;
    reveal?.cancel();
    transition?.skipTransition();
    reveal = transition = null;
    applyTheme(intendedDark);
  }
  reduced.addEventListener('change', () => { if (reduced.matches) settle(); });
  addEventListener('resize', () => { if (transition) settle(); }, {passive:true});
  addEventListener('pagehide', settle);
})();
