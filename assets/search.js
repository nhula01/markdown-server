(() => {
  const script = document.currentScript;
  const indexURL = new URL('../search-index.json', script.src);
  const dialog = document.getElementById('notebook-search');
  const input = document.getElementById('search-query');
  const results = document.getElementById('search-results');
  const status = document.getElementById('search-status');
  let entries, loading, previousFocus;
  const normalize = (text) => text.normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase();

  async function load() {
    if (!loading) {
      loading = fetch(indexURL, {cache: 'no-store'}).then(response => {
        if (!response.ok) throw new Error('Search index unavailable');
        return response.json();
      }).then(data => {
        entries = data.map(entry => ({...entry,
          haystack: normalize([entry.title, entry.category, entry.summary, ...entry.tags, entry.text].join(' '))}));
      }).catch(() => {
        loading = null;
        status.textContent = 'Search could not load. Close and reopen to retry, or browse Notes.';
      });
    }
    await loading;
  }

  function snippet(entry, tokens) {
    const text = [entry.summary, entry.text].join(' ').replace(/\s+/g, ' ').trim();
    const match = tokens.map(token => normalize(text).indexOf(token)).filter(index => index >= 0);
    let start = match.length ? Math.max(0, Math.min(...match) - 45) : 0;
    if (start) start = text.lastIndexOf(' ', start) + 1;
    return (start ? '…' : '') + text.slice(start, start + 185) + (text.length > start + 185 ? '…' : '');
  }

  function render() {
    if (!entries) return;
    results.replaceChildren();
    const tokens = normalize(input.value).trim().split(/\s+/).filter(Boolean);
    if (!tokens.length) {
      status.textContent = 'Type to search titles, chapter context, tags, and Optimum guides.';
      return;
    }
    const matches = entries.filter(entry => tokens.every(token => entry.haystack.includes(token)))
      .map(entry => ({entry, score: tokens.reduce((sum, token) => sum
        + (normalize(entry.title).includes(token) ? 10 : 0)
        + (entry.tags.some(tag => normalize(tag).includes(token)) ? 4 : 0)
        + (normalize(entry.summary).includes(token) ? 2 : 0), 0)}))
      .sort((a, b) => b.score - a.score || a.entry.title.localeCompare(b.entry.title));
    status.textContent = matches.length ? `${matches.length} result${matches.length === 1 ? '' : 's'}`
      : 'No matching notes yet. Try another word or browse the topic outlines.';
    for (const {entry} of matches.slice(0, 30)) {
      const item = document.createElement('li');
      const link = document.createElement('a');
      link.href = entry.url;
      const location = document.createElement('small');
      location.textContent = entry.category === entry.status ? entry.category : `${entry.category} › ${entry.status}`;
      const title = document.createElement('strong'); title.textContent = entry.title;
      const excerpt = document.createElement('span'); excerpt.textContent = snippet(entry, tokens);
      link.append(location, title, excerpt); item.append(link); results.append(item);
    }
  }

  async function open() {
    previousFocus = document.activeElement;
    dialog.showModal(); input.focus();
    if (!entries) status.textContent = 'Loading the notebook…';
    await load(); render();
  }
  document.querySelectorAll('[data-search-open]').forEach(button => button.addEventListener('click', open));
  document.querySelector('[data-search-close]').addEventListener('click', () => dialog.close());
  dialog.addEventListener('close', () => previousFocus?.focus());
  dialog.addEventListener('click', event => {if (event.target === dialog) dialog.close();});
  input.addEventListener('input', render);
  input.addEventListener('keydown', event => {
    if (event.key === 'Enter') {
      const first = results.querySelector('a');
      if (first) {event.preventDefault(); first.click();}
    }
  });
  document.addEventListener('keydown', event => {
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
      event.preventDefault(); dialog.open ? dialog.close() : open();
    }
  });
  dialog.addEventListener('keydown', event => {
    if (!['ArrowDown', 'ArrowUp'].includes(event.key)) return;
    const links = [...results.querySelectorAll('a')];
    if (!links.length) return;
    event.preventDefault();
    const index = links.indexOf(document.activeElement);
    if (event.key === 'ArrowDown') links[Math.min(index + 1, links.length - 1)].focus();
    else if (index <= 0) input.focus();
    else links[index - 1].focus();
  });
  document.querySelectorAll('[data-pdf-page]').forEach(link => link.addEventListener('click', event => {
    const reader = document.querySelector('.pdf-reader');
    const frame = document.querySelector('.chapter .pdf-frame');
    if (!reader && !frame) return;
    event.preventDefault();
    if (reader) {
      reader.dataset.page = link.dataset.pdfPage;
      reader.dispatchEvent(new CustomEvent('chapter-pdf-page', {detail: Number(link.dataset.pdfPage)}));
    } else frame.src = link.href;
    document.querySelectorAll('[data-pdf-page]').forEach(item => item.removeAttribute('aria-current'));
    link.setAttribute('aria-current', 'true');
    document.getElementById('handwritten-notes').scrollIntoView({behavior: 'auto', block: 'start'});
  }));
})();
