/* Section navigation is a progressive enhancement; links work without JS. */
(() => {
  const rail = document.querySelector('.home-section-rail');
  if (!rail) return;
  const links = [...rail.querySelectorAll('a[href^="#"]')];
  const sections = links.map(link => ({link, target:document.querySelector(link.hash)})).filter(item => item.target);
  let frame = 0, active = -1;
  function update() {
    frame = 0;
    let index = 0;
    sections.forEach((item, i) => { if (item.target.getBoundingClientRect().top <= innerHeight * .34) index = i; });
    if (scrollY + innerHeight >= document.documentElement.scrollHeight - 4) index = sections.length - 1;
    if (index === active) return;
    active = index;
    sections.forEach((item, i) => {
      if (i === index) item.link.setAttribute('aria-current', 'location');
      else item.link.removeAttribute('aria-current');
    });
    rail.style.setProperty('--rail-index', String(index));
  }
  function schedule() { if (!frame) frame = requestAnimationFrame(update); }
  addEventListener('scroll', schedule, {passive:true});
  addEventListener('resize', schedule, {passive:true});
  addEventListener('pageshow', schedule);
  addEventListener('load', schedule);
  addEventListener('pagehide', () => { cancelAnimationFrame(frame); frame = 0; });
  if ('ResizeObserver' in window) new ResizeObserver(schedule).observe(document.querySelector('.home-main'));
  document.fonts?.ready.then(schedule);
  schedule();
})();
