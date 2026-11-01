/* Chapter tabs remain ordinary links; scroll feedback is a small enhancement. */
(() => {
  const menus = [...document.querySelectorAll('[data-section-nav]')].map(nav => ({
    nav, items:[...nav.querySelectorAll('a[href^="#"]')].map(link => ({link,target:document.getElementById(decodeURIComponent(link.hash.slice(1)))})).filter(item => item.target)
  })).filter(menu => menu.items.length);
  if (!menus.length) return;
  let frame = 0;
  function update() {
    frame = 0;
    for (const {items} of menus) {
      let current = items[0];
      const margin = parseFloat(getComputedStyle(items[0].target).scrollMarginTop) || 0;
      const padding = parseFloat(getComputedStyle(document.documentElement).scrollPaddingTop) || 0;
      const edge = Math.max(150,margin+padding+8);
      for (const item of items) { if (item.target.getBoundingClientRect().top <= edge) current = item; }
      if (scrollY + innerHeight >= document.documentElement.scrollHeight-4) {
        // Several short sections can share the bottom of the viewport. Respect
        // an explicitly chosen, visible anchor instead of always selecting last.
        const anchored = items.find(item => item.link.hash === location.hash);
        const bounds = anchored?.target.getBoundingClientRect();
        current = bounds && bounds.top < innerHeight && bounds.bottom > 0 ? anchored : items[items.length-1];
      }
      for (const item of items) {
        if (item === current) item.link.setAttribute('aria-current','location');
        else item.link.removeAttribute('aria-current');
      }
    }
  }
  function schedule() { if (!frame) frame=requestAnimationFrame(update); }
  addEventListener('scroll',schedule,{passive:true});addEventListener('resize',schedule,{passive:true});addEventListener('pageshow',schedule);addEventListener('load',schedule);addEventListener('hashchange',schedule);
  addEventListener('pagehide',()=>{cancelAnimationFrame(frame);frame=0;});
  if ('ResizeObserver' in window) new ResizeObserver(schedule).observe(document.querySelector('.interior-main'));
  schedule();
})();
