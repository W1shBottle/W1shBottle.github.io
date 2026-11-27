/* Progressive enhancement for the learning dashboard:
 * - Without JS: native <details> stages & tasks remain completely readable.
 * - With JS: stages become a compact segmented tab strip directly above an
 *   in-place task workspace so clicking any stage reveals its tasks immediately
 *   with zero scrolling and zero empty layout voids.
 */
(() => {
  const root = document.querySelector('[data-learning-dashboard]');
  if (!root) return;
  const motion = matchMedia('(prefers-reduced-motion: reduce)');
  const duration = 280;
  const controllers = new Map();

  // Smooth disclosure controller for task evidence, optional tasks, and calculation details.
  root.querySelectorAll('details').forEach(details => {
    const summary = details.querySelector(':scope > summary');
    if (!summary) return;
    const body = document.createElement('div');
    const inner = document.createElement('div');
    body.className = 'journey-disclosure-body';
    inner.className = 'journey-disclosure-inner';
    [...details.childNodes].filter(node => node !== summary).forEach(node => inner.append(node));
    body.append(inner);
    details.append(body);
    details.dataset.disclosureReady = '';
    let expanded = details.open;
    let timer = 0;
    let running = false;

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
      const start = body.getBoundingClientRect().height;
      clearTimeout(timer);
      body.style.transition = 'none';
      body.style.height = start + 'px';
      expanded = next;
      details.open = true;
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
      void body.offsetHeight;
      body.style.removeProperty('transition');
      body.style.height = end + 'px';
      timer = setTimeout(finish, duration + 80);
    }

    details.dataset.expanded = String(expanded);
    summary.setAttribute('aria-expanded', String(expanded));
    finish();
    summary.addEventListener('click', event => {
      if (event.target.closest('a,button,input,select,textarea')) return;
      event.preventDefault();
      setOpen(!expanded);
    });
    body.addEventListener('transitionend', event => {
      if (event.target === body && event.propertyName === 'height') finish();
    });
    details.addEventListener('toggle', () => {
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
    controllers.set(details, { setOpen, finish, inner, summary });
  });

  // Transform .journey-stages into a compact top tab strip + instant in-place workspace.
  const stagesEl = root.querySelector('.journey-stages');
  const stageCards = stagesEl ? [...stagesEl.querySelectorAll(':scope > .journey-stage')] : [];
  const stageIndex = new Map();
  let tabStrip = null;
  let workspace = null;
  let activeStageId = null;

  if (stagesEl && stageCards.length) {
    const shell = document.createElement('div');
    shell.className = 'journey-stage-explorer';

    tabStrip = document.createElement('div');
    tabStrip.className = 'journey-stage-tabs';
    tabStrip.setAttribute('role', 'tablist');
    tabStrip.setAttribute('aria-label', '阶段路线切换');

    workspace = document.createElement('div');
    workspace.className = 'journey-stage-workspace';

    stageCards.forEach((card, idx) => {
      const stageId = card.id || `stage-${idx}`;
      const ctrl = controllers.get(card);
      const list = ctrl?.inner.querySelector(':scope > .journey-tasks');
      if (!list) return;

      const code = card.querySelector('.journey-stage-code')?.textContent?.trim() || '';
      const title = card.querySelector('.journey-stage-title')?.textContent?.trim() || '';
      const desc = card.querySelector('.journey-stage-description')?.textContent?.trim() || '';
      const badgeEl = card.querySelector('.journey-badge');
      const badgeText = badgeEl?.textContent?.trim() || '';
      const badgeClass = badgeEl?.className || 'journey-badge badge-planned';
      const progressLabel = card.querySelector('.journey-stage-progress-label > span')?.textContent?.trim() || '';
      const percentText = card.querySelector('.journey-stage-progress-label strong')?.textContent?.trim() || '0%';
      const startedText = card.querySelector('.journey-stage-started')?.textContent?.trim() || '';
      const acceptedBar = card.querySelector('.journey-stage-track .journey-meter-accepted');
      const practicingBar = card.querySelector('.journey-stage-track .journey-meter-practicing');
      const acceptedWidth = acceptedBar?.style.width || '0%';
      const practicingWidth = practicingBar?.style.width || '0%';
      const isCurrent = card.classList.contains('is-current');
      const isComplete = badgeClass.includes('badge-complete');
      const isStarted = badgeClass.includes('badge-active');

      // Extract compact metric for tab (e.g. "60%" or "5/10")
      const startedFraction = startedText.match(/(\d+\s*\/\s*\d+)/)?.[1]?.replace(/\s+/g, '') || '';
      const tabMetric = percentText !== '0%' ? percentText : (startedFraction || percentText);

      // Build compact tab button
      const tab = document.createElement('button');
      tab.type = 'button';
      tab.className = 'journey-stage-tab' + (isCurrent ? ' is-current' : '');
      tab.setAttribute('role', 'tab');
      tab.id = `tab-${stageId}`;
      tab.setAttribute('aria-controls', stageId);
      tab.setAttribute('aria-selected', 'false');
      tab.setAttribute('tabindex', '-1');

      const tabTop = document.createElement('span');
      tabTop.className = 'journey-tab-top';
      const tabCodeWrap = document.createElement('span');
      tabCodeWrap.className = 'journey-tab-code';
      const dot = document.createElement('i');
      dot.className = 'journey-tab-dot ' + (isComplete ? 'is-complete' : isStarted ? 'is-active' : 'is-planned');
      dot.setAttribute('aria-hidden', 'true');
      tabCodeWrap.append(dot, document.createTextNode(code));

      const tabStat = document.createElement('span');
      tabStat.className = 'journey-tab-stat';
      tabStat.textContent = tabMetric;
      tabTop.append(tabCodeWrap, tabStat);

      const tabTitle = document.createElement('span');
      tabTitle.className = 'journey-tab-title';
      tabTitle.textContent = title;

      const tabBar = document.createElement('span');
      tabBar.className = 'journey-tab-bar';
      tabBar.setAttribute('aria-hidden', 'true');
      const tabAcc = document.createElement('span');
      tabAcc.className = 'journey-meter-accepted';
      tabAcc.style.width = acceptedWidth;
      const tabPrac = document.createElement('span');
      tabPrac.className = 'journey-meter-practicing';
      tabPrac.style.width = practicingWidth;
      tabBar.append(tabAcc, tabPrac);

      tab.append(tabTop, tabTitle, tabBar);
      tab.addEventListener('click', () => activateStage(stageId));
      tab.addEventListener('keydown', event => {
        const ids = [...stageIndex.keys()];
        const currentPos = ids.indexOf(stageId);
        let nextPos = -1;
        if (event.key === 'ArrowRight' || event.key === 'ArrowDown') nextPos = (currentPos + 1) % ids.length;
        else if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') nextPos = (currentPos - 1 + ids.length) % ids.length;
        else if (event.key === 'Home') nextPos = 0;
        else if (event.key === 'End') nextPos = ids.length - 1;
        if (nextPos >= 0) {
          event.preventDefault();
          const nextId = ids[nextPos];
          activateStage(nextId);
          stageIndex.get(nextId)?.tab.focus();
        }
      });
      tabStrip.append(tab);

      // Build open editorial stage panel directly beneath the tab strip
      // Move the canonical stage ID onto the panel so #stage-* deep links land cleanly here.
      card.removeAttribute('id');
      const panel = document.createElement('section');
      panel.className = 'journey-stage-panel';
      panel.id = stageId;
      panel.setAttribute('role', 'tabpanel');
      panel.setAttribute('aria-labelledby', tab.id);
      panel.hidden = true;

      const head = document.createElement('div');
      head.className = 'journey-panel-head';

      const headMain = document.createElement('div');
      headMain.className = 'journey-panel-main';
      const titleRow = document.createElement('div');
      titleRow.className = 'journey-panel-title-row';
      const codePill = document.createElement('span');
      codePill.className = 'journey-stage-code';
      codePill.textContent = code;
      const h4 = document.createElement('h4');
      h4.textContent = title;
      const badge = document.createElement('span');
      badge.className = badgeClass;
      badge.innerHTML = `<i aria-hidden="true"></i>${badgeText}`;
      titleRow.append(codePill, h4, badge);

      const descEl = document.createElement('p');
      descEl.className = 'journey-panel-desc';
      descEl.textContent = desc;
      headMain.append(titleRow, descEl);

      const headStats = document.createElement('div');
      headStats.className = 'journey-panel-stats';
      const scoreRow = document.createElement('div');
      scoreRow.className = 'journey-panel-score';
      scoreRow.innerHTML = `<strong>${percentText}</strong><span>${progressLabel}</span>`;
      const track = document.createElement('div');
      track.className = 'journey-stage-track';
      track.setAttribute('aria-hidden', 'true');
      const pAcc = document.createElement('span');
      pAcc.className = 'journey-meter-accepted';
      pAcc.style.width = acceptedWidth;
      const pPrac = document.createElement('span');
      pPrac.className = 'journey-meter-practicing';
      pPrac.style.width = practicingWidth;
      track.append(pAcc, pPrac);
      const startedEl = document.createElement('p');
      startedEl.className = 'journey-panel-started';
      startedEl.textContent = startedText;
      headStats.append(scoreRow, track, startedEl);

      head.append(headMain, headStats);
      panel.append(head, list);
      workspace.append(panel);

      stageIndex.set(stageId, { tab, panel, isCurrent });
    });

    shell.append(tabStrip, workspace);
    stagesEl.before(shell);
    stagesEl.dataset.stageTabs = 'ready';
    stagesEl.hidden = true;

    const initialId =
      [...stageIndex.entries()].find(([, entry]) => entry.isCurrent)?.[0] ||
      stageIndex.keys().next().value;
    if (initialId) activateStage(initialId, false);
  }

  function activateStage(stageId, animate = true) {
    if (!stageIndex.has(stageId)) return;
    activeStageId = stageId;
    stageIndex.forEach(({ tab, panel }, id) => {
      const selected = id === stageId;
      tab.setAttribute('aria-selected', String(selected));
      tab.setAttribute('tabindex', selected ? '0' : '-1');
      tab.classList.toggle('is-selected', selected);
      panel.hidden = !selected;
      if (selected && animate && !motion.matches) {
        panel.classList.remove('is-entering');
        void panel.offsetWidth;
        panel.classList.add('is-entering');
      }
    });
  }

  window.addEventListener('resize', () => controllers.forEach(c => c.finish()), { passive: true });
  motion.addEventListener('change', () => controllers.forEach(c => c.finish()));

  function revealTarget() {
    let id;
    try { id = decodeURIComponent(location.hash.slice(1)); } catch { return; }
    const target = document.getElementById(id);
    if (!target || !root.contains(target)) return;

    if (stageIndex.has(id)) {
      activateStage(id, false);
      requestAnimationFrame(() => tabStrip?.scrollIntoView({ block: 'start' }));
      return;
    }

    const ownerPanel = target.closest('.journey-stage-panel');
    if (ownerPanel && stageIndex.has(ownerPanel.id)) {
      activateStage(ownerPanel.id, false);
    }

    const detail = target.querySelector(':scope > details');
    if (detail) controllers.get(detail)?.setOpen(true, false);
    let node = target;
    while (node && node !== root) {
      if (node.tagName === 'DETAILS') controllers.get(node)?.setOpen(true, false);
      node = node.parentElement;
    }
    requestAnimationFrame(() => target.scrollIntoView({ block: 'start' }));
  }

  root.addEventListener('click', event => {
    const link = event.target.closest('a[href^="#"]');
    if (link && link.hash === location.hash) revealTarget();
  });
  window.addEventListener('hashchange', revealTarget);
  revealTarget();
})();
