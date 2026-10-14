/* Progressive enhancement: without JavaScript, every record remains readable. */
(() => {
  const root = document.querySelector('[data-learning-progress]');
  if (!root) return;
  const entries = [...root.querySelectorAll('.progress-entry')];
  const filters = [...root.querySelectorAll('[data-project-filter]')];
  const more = root.querySelector('.progress-more');
  const count = root.querySelector('.progress-visible-count');
  const limit = 3;
  let project = 'all';
  let expanded = false;
  function render() {
    const matching = entries.filter(entry => project === 'all' || entry.dataset.project === project);
    const visible = new Set(expanded ? matching : matching.slice(0, limit));
    entries.forEach(entry => { entry.hidden = !visible.has(entry); });
    filters.forEach(button => button.setAttribute('aria-pressed', String(button.dataset.projectFilter === project)));
    more.hidden = matching.length <= limit;
    more.setAttribute('aria-expanded', String(expanded));
    more.textContent = expanded ? '收起较早记录' : '展开更早记录（' + Math.max(0, matching.length - limit) + '）';
    count.textContent = '显示 ' + visible.size + ' 条，共 ' + matching.length + ' 条记录';
  }
  filters.forEach(button => button.addEventListener('click', () => {
    project = button.dataset.projectFilter;
    expanded = false;
    render();
  }));
  more.addEventListener('click', () => {
    const collapsing = expanded;
    expanded = !expanded;
    render();
    if (collapsing) root.querySelector('.progress-filters').scrollIntoView({block: 'nearest'});
  });
  root.querySelector('.progress-filters').hidden = false;
  root.querySelector('.progress-footer').hidden = false;
  render();
})();
