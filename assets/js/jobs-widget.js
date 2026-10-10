(() => {
  const widget = document.querySelector('.jobs-widget');
  if (!widget) return;
  const slide = widget.querySelector('.jobs-slide'), status = widget.querySelector('.jobs-status');
  const controls = widget.querySelector('.jobs-controls'), count = widget.querySelector('.jobs-count');
  const pause = widget.querySelector('[data-action="pause"]');
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  let paused = reduced.matches, hovered = false, focused = false, position = 0, jobs = [], feed, loading = false;
  const data = window.WishJobs;
  let selectionDay = '';
  const date = new Intl.DateTimeFormat('zh-CN', {timeZone:'Asia/Shanghai', month:'2-digit', day:'2-digit', hour:'2-digit', minute:'2-digit', hour12:false});
  function safeLink(value) {
    return data.safeLink(value);
  }
  function element(tag, className, text) {
    const node = document.createElement(tag); node.className = className; if (text) node.textContent = text; return node;
  }
  function link(text, url, className) {
    const node = element('a', className, text); node.href = safeLink(url); node.target = '_blank'; node.rel = 'noopener noreferrer'; return node;
  }
  function valid(job) {
    return data.eligible(job);
  }
  function setPause() {
    pause.textContent = paused ? '播放' : '暂停';
    pause.setAttribute('aria-label', paused ? '开始自动轮播' : '暂停自动轮播');
  }
  function render(manual = false) {
    slide.setAttribute('aria-live', manual ? 'polite' : 'off');
    slide.replaceChildren(); controls.hidden = jobs.length < 2;
    if (!jobs.length) {
      slide.append(element('p', 'jobs-empty', '暂时没有可确认的新岗位。'), link('去招聘官网看看 ↗', 'https://dptech.zhiye.com/jobs', 'jobs-original'));
      return;
    }
    position = (position + jobs.length) % jobs.length;
    const job = jobs[position];
    const heading = element('h3', 'jobs-title'); heading.append(link(job.title, job.url, ''));
    const meta = element('p', 'jobs-meta', `${job.company} · ${job.locations?.join(' / ') || '杭州'} · ${job.type}`);
    const tags = element('div', 'jobs-tags');
    for (const skill of (job.skills || []).slice(0,4)) if (typeof skill === 'string') tags.append(element('span', '', skill));
    const facts = element('p','jobs-facts',`${job.education || '学历见原文'} · ${job.cohort || '届别见原文'} · 薪资${job.salary || '未公布'}`);
    const info = element('div', 'jobs-info'); info.append(heading,meta,facts,tags);
    const source = element('div', 'jobs-source'); source.append(link('查看原文 ↗',job.url,'jobs-original'), element('span','',`来源：${job.source}`),element('span','',`发布：${job.publishedAt || '未提供'}`));
    slide.append(info,source); count.textContent = `${position + 1} / ${jobs.length}`; setPause();
  }
  function apply(next) {
    if (next.schemaVersion !== 1 || !Array.isArray(next.jobs) || !Array.isArray(next.sources)) throw new Error('Invalid feed');
    feed = next;
    const current = jobs[position]?.id;
    const all = next.jobs.filter(valid), now = Date.now(), today = data.dayKey(now);
    jobs = data.daily(all,now);
    position = selectionDay === today ? Math.max(0, jobs.findIndex(job => job.id === current)) : 0;
    selectionDay = today;
    const activity = data.changes(all,now);
    widget.querySelector('.jobs-overview').textContent = `${new Set(all.map(job=>job.company)).size} 家企业 · ${all.length} 个岗位 · ${activity.added ? `今日新收录 ${activity.added} 个` : '今日暂无新收录'}${activity.changed ? ` · 信息更新 ${activity.changed} 个` : ''}`;
    widget.querySelector('.jobs-scope').textContent = `${today.slice(5).replace('-','/')} 推荐`;
    const dates = jobs.map(job => Date.parse(job.checkedAt));
    const last = dates.length ? Math.min(...dates) : NaN;
    const failed = next.sources.some(source => source.status !== 'ok');
    status.textContent = Number.isFinite(last) ? `${failed ? '部分来源同步失败 · ' : ''}${date.format(last)} 同步${Date.now() - last > 3*3600000 ? ' · 等待更新' : ''}` : (failed ? '来源暂时不可用，请查看招聘官网。' : '当前暂无匹配岗位。');
    render();
  }
  async function refresh() {
    if (loading) return;
    loading = true;
    try {
      const response = await fetch(widget.dataset.feed, {cache:'no-store',signal:AbortSignal.timeout(10000)});
      if (!response.ok) throw new Error('Feed unavailable');
      apply(await response.json());
    } catch {
      if (feed) apply(feed); else render();
      status.textContent = jobs.length ? '更新暂不可用 · 正在展示上次同步的岗位' : '岗位信息暂时无法加载，请查看招聘官网。';
    } finally { loading = false; }
  }
  controls.addEventListener('click', event => {
    const action = event.target.closest('button')?.dataset.action;
    if (action === 'pause') { paused = !paused; setPause(); }
    if (action === 'previous' || action === 'next') { position += action === 'next' ? 1 : -1; render(true); }
  });
  widget.addEventListener('mouseenter', () => { hovered = true; });
  widget.addEventListener('mouseleave', () => { hovered = false; });
  widget.addEventListener('focusin', () => { focused = true; });
  widget.addEventListener('focusout', event => { focused = widget.contains(event.relatedTarget); });
  reduced.addEventListener('change', event => { if(event.matches) {paused=true;setPause();} });
  setInterval(() => {
    if (!document.hidden && !paused && !hovered && !focused && jobs.length > 1) { position++; render(); }
  }, 7000);
  // Expire stale records even when the tab stays open during a network outage.
  setInterval(() => { if (feed && (jobs.some(job=>!valid(job)) || selectionDay !== data.dayKey(Date.now()))) apply(feed); }, 60000);
  setInterval(() => { if (!document.hidden) refresh(); }, 10*60000);
  document.addEventListener('visibilitychange', () => { if (!document.hidden) refresh(); });
  refresh();
})();
