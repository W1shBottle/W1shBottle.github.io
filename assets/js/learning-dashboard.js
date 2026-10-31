/* Native details keep the full dashboard readable without JavaScript. */
(() => {
  const root = document.querySelector('[data-learning-dashboard]');
  if (!root) return;
  function revealTarget() {
    let id;
    try { id = decodeURIComponent(location.hash.slice(1)); } catch { return; }
    const target = document.getElementById(id);
    if (!target || !root.contains(target)) return;
    let node = target;
    while (node && node !== root) {
      if (node.tagName === 'DETAILS') node.open = true;
      node = node.parentElement;
    }
    const detail = target.querySelector(':scope > details');
    if (detail) detail.open = true;
    requestAnimationFrame(() => target.scrollIntoView({block: 'start'}));
  }
  root.addEventListener('click', event => {
    const link = event.target.closest('a[href^="#"]');
    if (link && link.hash === location.hash) revealTarget();
  });
  window.addEventListener('hashchange', revealTarget);
  revealTarget();
})();
