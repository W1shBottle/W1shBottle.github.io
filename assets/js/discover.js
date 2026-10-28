(() => {
  const page = document.querySelector('.discovery-page');
  if (!page) return;
  const controls = page.querySelector('[data-discovery-controls]');
  if (!controls) return;
  const cards = [...page.querySelectorAll('.discovery-card')];
  const buttons = [...page.querySelectorAll('[data-discovery-filter]')];
  const search = page.querySelector('[data-discovery-search]');
  const count = page.querySelector('[data-discovery-count]');
  const empty = page.querySelector('[data-discovery-empty]');
  let category = 'all';
  function update() {
    const query = search.value.trim().toLocaleLowerCase();
    let visible = 0;
    for (const card of cards) {
      const match = (category === 'all' || card.dataset.category === category)
        && card.textContent.toLocaleLowerCase().includes(query);
      card.hidden = !match;
      if (match) visible++;
    }
    for (const button of buttons) button.setAttribute('aria-pressed', String(button.dataset.discoveryFilter === category));
    count.hidden = category === 'all' && !query;
    count.textContent = `本期匹配 ${visible} / ${cards.length} 个项目`;
    empty.hidden = visible !== 0;
  }
  for (const button of buttons) button.addEventListener('click', () => {
    category = button.dataset.discoveryFilter;
    update();
  });
  search.addEventListener('input', update);
  page.querySelector('[data-discovery-reset]').addEventListener('click', () => {
    category = 'all'; search.value = ''; update(); search.focus();
  });
  controls.hidden = false;
})();
