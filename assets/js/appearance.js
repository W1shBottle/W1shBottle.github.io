/*! WishBottle navigation and reading interactions.
 * Spring adapted from Lens / design-systems by DayDreamInAReverie (c) 2026.
 * MIT License: see /licenses/lens.txt. Source: design-systems / internal/jelly-physics.js.
 */
(() => {
  'use strict';
  class Spring {
    constructor(value = 0) { this.value = value; this.velocity = 0; this.target = value; }
    step(dt, stiffness = 220, damping = 20) {
      let remaining = Math.min(Math.max(dt, 0), .08);
      while (remaining > 0) {
        const h = Math.min(remaining, 1 / 180);
        this.velocity += ((this.target - this.value) * stiffness - this.velocity * damping) * h;
        this.value += this.velocity * h;
        remaining -= h;
      }
      if (Math.abs(this.velocity) < .025 && Math.abs(this.target - this.value) < .005) {
        this.value = this.target; this.velocity = 0;
      }
      return this.value;
    }
    snap(value = this.target) { this.value = this.target = value; this.velocity = 0; }
    get moving() { return Math.abs(this.velocity) > .025 || Math.abs(this.target - this.value) > .005; }
  }
  const motionPreference = matchMedia('(prefers-reduced-motion: reduce)');
  const hoverPreference = matchMedia('(hover: hover)');
  const effects = new Set();
  const animateOnce = (element, frames, options) => {
    if (motionPreference.matches) return null;
    const animation = element.animate(frames, options);
    effects.add(animation);
    animation.finished.then(() => { effects.delete(animation); animation.cancel(); }, () => effects.delete(animation));
    return animation;
  };

  function capsule(container, selector, selectedSelector) {
    if (!container) return {select() {}, sync() {}, stop() {}};
    const items = [...container.querySelectorAll(selector)];
    const pill = document.createElement('span');
    pill.className = 'motion-capsule';
    pill.setAttribute('aria-hidden', 'true');
    container.prepend(pill);
    container.classList.add('has-capsule');
    const springs = ['x', 'y', 'width', 'height'].map(() => new Spring());
    let current = container.querySelector(selectedSelector) || items[0];
    let frame = 0, previous = 0, initialized = false, visible = false;
    function paint() {
      const [x, y, width, height] = springs.map(s => s.value);
      const stretch = motionPreference.matches ? 1 : 1 + Math.min(Math.abs(springs[0].velocity) / 18000, .025);
      pill.style.width = `${Math.max(0, width)}px`;
      pill.style.height = `${Math.max(0, height)}px`;
      pill.style.transform = `translate3d(${x}px,${y}px,0) scale(${stretch},${1 / stretch})`;
    }
    function tick(time) {
      const dt = previous ? (time - previous) / 1000 : 1 / 60;
      previous = time;
      springs.forEach(s => s.step(dt, 260, 25));
      paint();
      if (springs.some(s => s.moving)) {
        frame = requestAnimationFrame(tick);
      } else {
        frame = 0; previous = 0;
        container.dataset.motion = 'rest';
      }
    }
    function target(item, immediate = false) {
      if (!item || !container.getClientRects().length) return;
      current = item;
      visible = true;
      pill.style.opacity = "1";
      const values = [item.offsetLeft, item.offsetTop, item.offsetWidth, item.offsetHeight];
      values.forEach((value, i) => { springs[i].target = value; });
      if (immediate || !initialized || motionPreference.matches) {
        cancelAnimationFrame(frame); frame = 0; previous = 0;
        springs.forEach(s => s.snap()); paint();
        container.dataset.motion = 'rest';
      } else if (!frame) {
        container.dataset.motion = 'running';
        frame = requestAnimationFrame(tick);
      }
      initialized = true;
    }
    function restore() {
      const focused = items.find(item => item === document.activeElement);
      const selected = focused || container.querySelector(selectedSelector);
      if (selected) target(selected);
      else {
        cancelAnimationFrame(frame); frame = 0; previous = 0; visible = false;
        pill.style.opacity = '0'; container.dataset.motion = 'rest';
      }
    }
    items.forEach(item => {
      item.addEventListener('pointerenter', () => { if (hoverPreference.matches) target(item); });
      item.addEventListener('focus', () => target(item));
    });
    container.addEventListener('pointerleave', restore);
    container.addEventListener('focusout', () => queueMicrotask(restore));
    if (container.querySelector(selectedSelector)) target(current, true);
    else { pill.style.opacity = "0"; container.dataset.motion = "rest"; }
    const controller = {
      select: restore,
      sync: () => { if (visible) target(current, true); },
      stop: () => { cancelAnimationFrame(frame); frame = 0; previous = 0; }
    };
    new ResizeObserver(controller.sync).observe(container);
    return controller;
  }
  const navMotion = capsule(document.querySelector('.site-nav'), 'a', '[aria-current="page"]');
  const filterContainer = document.querySelector('.progress-filters');
  const filterMotion = capsule(filterContainer, 'button', '[aria-pressed="true"]');
  filterContainer?.addEventListener('click', () => filterMotion.select());
  const capsules = [navMotion, filterMotion];

  const themeButton = document.getElementById('theme');
  function setTheme(dark, save = true) {
    document.documentElement.dataset.theme = dark ? 'dark' : 'light';
    document.documentElement.style.colorScheme = dark ? 'dark' : 'light';
    document.body.classList.remove('light', 'dark');
    document.body.classList.add(dark ? 'dark' : 'light');
    themeButton.setAttribute('aria-pressed', String(dark));
    themeButton.setAttribute('aria-label', dark ? '切换浅色主题' : '切换 One Dark 主题');
    themeButton.querySelector('.theme-label').textContent = dark ? 'One Dark' : '浅色';
    if (save) { try { localStorage.setItem('wish-typo-theme', dark ? 'dark' : 'light'); } catch {} }
  }
  setTheme(document.documentElement.dataset.theme === 'dark', false);
  themeButton.addEventListener('click', () => setTheme(document.documentElement.dataset.theme !== 'dark'));

  if (matchMedia('(min-width: 1100px)').matches) document.querySelectorAll('.article-toc').forEach(toc => { toc.open = true; });

  const disclosureControllers = [...document.querySelectorAll('.series-item, .post-series, .toc, .progress-evidence, .learning-context')].map(details => {
    const summary = details.querySelector('summary');
    let content = details.querySelector('.series-chapters, .post-series-content');
    if (!content) {
      content = document.createElement('div');
      content.className = 'motion-detail-content';
      [...details.childNodes].filter(node => node !== summary).forEach(node => content.append(node));
      details.append(content);
    }
    let expanded = details.open, heightAnimation = null, contentAnimation = null, generation = 0;
    details.dataset.expanded = String(expanded);
    function cancel() {
      heightAnimation?.cancel(); contentAnimation?.cancel();
      heightAnimation = contentAnimation = null;
    }
    function finish() {
      generation++;
      cancel();
      details.open = expanded;
      details.dataset.expanded = String(expanded);
      content.inert = !expanded;
      details.style.removeProperty('height');
      details.style.removeProperty('overflow');
      details.dataset.motion = 'rest';
    }
    function toggle() {
      const startHeight = details.getBoundingClientRect().height;
      const wasOpen = details.open;
      const startOpacity = wasOpen ? Number(getComputedStyle(content).opacity) : 0;
      expanded = !expanded;
      const token = ++generation;
      cancel();
      details.dataset.expanded = String(expanded);
      if (!expanded && content.contains(document.activeElement)) summary.focus();
      content.inert = !expanded;
      if (motionPreference.matches) { finish(); return; }
      // Measure natural destination synchronously; keep children rendered while closing.
      details.style.removeProperty('height');
      details.open = expanded;
      const endHeight = details.getBoundingClientRect().height;
      details.open = true;
      details.style.height = `${startHeight}px`;
      details.style.overflow = 'hidden';
      details.dataset.motion = 'running';
      heightAnimation = details.animate([
        {height: `${startHeight}px`}, {height: `${endHeight}px`}
      ], {duration: 360, easing: 'cubic-bezier(.2,.7,.2,1)', fill: 'forwards'});
      contentAnimation = content.animate([
        {opacity: startOpacity, transform: wasOpen ? 'translateY(0)' : 'translateY(4px)'},
        {opacity: expanded ? 1 : 0, transform: expanded ? 'translateY(0)' : 'translateY(4px)'}
      ], {duration: expanded ? 320 : 220, easing: 'ease-out', fill: 'forwards'});
      heightAnimation.finished.then(() => { if (generation === token) finish(); }, () => {});
    }
    summary.addEventListener('click', event => { event.preventDefault(); toggle(); });
    content.inert = !expanded;
    return {finish};
  });

  const revealElements = document.querySelectorAll('.hero>div, .featured, .compact-post, .project-panel, .series-item, .page-heading, .post-series, .note-entry, .learning-card, .progress-card');
  if ('IntersectionObserver' in window && !motionPreference.matches) {
    const observer = new IntersectionObserver(entries => {
      entries.filter(entry => entry.isIntersecting).forEach((entry, i) => {
        observer.unobserve(entry.target);
        animateOnce(entry.target, [
          {opacity: 0, transform: 'translateY(9px)'}, {opacity: 1, transform: 'translateY(0)'}
        ], {duration: 520, delay: Math.min(i * 45, 135), easing: 'cubic-bezier(.2,.7,.2,1)', fill: 'backwards'});
      });
    }, {threshold: .08});
    revealElements.forEach(element => observer.observe(element));
  }

  // Reading feedback is updated only when a frame is needed; no idle animation loop.
  const readingBody = document.getElementById('article-body');
  const progressBar = document.querySelector('.reading-progress');
  const backToTop = document.querySelector('.back-to-top');
  const rail = document.querySelector('.article-rail');
  const sectionLinks = [...document.querySelectorAll('.article-toc #TableOfContents > ul > li > a')];
  const sections = sectionLinks.map(link => {
    let id;
    try { id = decodeURIComponent(link.hash.slice(1)); } catch { return null; }
    const heading = document.getElementById(id);
    return heading ? {link, heading} : null;
  }).filter(Boolean);
  let feedbackFrame = 0, previousPercent = -1, activeSection = null;
  function updateReading() {
    feedbackFrame = 0;
    if (backToTop) backToTop.hidden = scrollY < 560;
    if (!readingBody || !progressBar) return;
    const bounds = readingBody.getBoundingClientRect();
    const start = bounds.top + scrollY - 130;
    const end = bounds.bottom + scrollY - innerHeight;
    const fraction = Math.max(0, Math.min(1, (scrollY - start) / Math.max(1, end - start)));
    const percent = Math.round(fraction * 100);
    progressBar.firstElementChild.style.transform = `scaleX(${fraction})`;
    if (percent !== previousPercent) {
      progressBar.setAttribute('aria-valuenow', String(percent));
      previousPercent = percent;
    }
    const activationLine = innerWidth > 760 ? 175 : 205;
    let current = sections[0];
    for (const section of sections) {
      if (section.heading.getBoundingClientRect().top <= activationLine) current = section;
      else break;
    }
    if (current && current !== activeSection) {
      sections.forEach(section => {
        if (section === current) section.link.setAttribute('aria-current', 'location');
        else section.link.removeAttribute('aria-current');
      });
      activeSection = current;
      if (rail && matchMedia('(min-width: 1100px)').matches && rail.querySelector('details').open) {
        const box = rail.getBoundingClientRect(), linkBox = current.link.getBoundingClientRect();
        if (linkBox.bottom > box.bottom - 25) rail.scrollTop += linkBox.bottom - box.bottom + 45;
        else if (linkBox.top < box.top + 40) rail.scrollTop -= box.top + 55 - linkBox.top;
      }
    }
  }
  function requestReading() { if (!feedbackFrame) feedbackFrame = requestAnimationFrame(updateReading); }
  addEventListener('scroll', requestReading, {passive: true});
  addEventListener('resize', requestReading, {passive: true});
  addEventListener('load', requestReading);
  addEventListener('pageshow', requestReading);
  backToTop?.addEventListener('click', () => {
    document.querySelector('.brand')?.focus({preventScroll: true});
    scrollTo({top: 0, behavior: motionPreference.matches ? 'instant' : 'smooth'});
  });
  requestReading();

  // Small local highlight: the surface responds to a pointer, then settles.
  const shineControllers = [...document.querySelectorAll('.project-panel, .series-item, .post-series-summary')].map(surface => {
    let frame = 0, point = null;
    const stop = () => { cancelAnimationFrame(frame); frame = 0; point = null; };
    surface.addEventListener('pointermove', event => {
      if (!hoverPreference.matches || motionPreference.matches) return;
      point = {x: event.clientX, y: event.clientY};
      if (frame) return;
      frame = requestAnimationFrame(() => {
        frame = 0;
        if (!point) return;
        const rect = surface.getBoundingClientRect();
        surface.style.setProperty('--shine-x', `${point.x - rect.left}px`);
        surface.style.setProperty('--shine-y', `${point.y - rect.top}px`);
      });
    }, {passive: true});
    surface.addEventListener('pointerleave', stop);
    return {stop};
  });
  motionPreference.addEventListener('change', () => shineControllers.forEach(controller => controller.stop()));
  addEventListener('pagehide', () => {
    cancelAnimationFrame(feedbackFrame); feedbackFrame = 0;
    shineControllers.forEach(controller => controller.stop());
  });

  const header = document.querySelector('.site-head');
  const scrollFeedback = () => header.classList.toggle('is-scrolled', scrollY > 70);
  addEventListener('scroll', scrollFeedback, {passive: true});
  scrollFeedback();
  addEventListener('resize', () => {
    disclosureControllers.forEach(controller => controller.finish());
    capsules.forEach(controller => controller.sync());
  }, {passive: true});
  motionPreference.addEventListener('change', () => {
    if (motionPreference.matches) effects.forEach(animation => animation.cancel());
    disclosureControllers.forEach(controller => controller.finish());
    capsules.forEach(controller => controller.sync());
  });
  document.fonts.ready.then(() => capsules.forEach(controller => controller.sync()));
  addEventListener('pagehide', () => {
    capsules.forEach(controller => controller.stop());
    effects.forEach(animation => animation.cancel());
    disclosureControllers.forEach(controller => controller.finish());
  });
  addEventListener('pageshow', () => capsules.forEach(controller => controller.sync()));
})();
