(() => {
  const script = document.currentScript;
  const query = document.getElementById('thread-query');
  const options = document.getElementById('thread-options');
  const clear = document.getElementById('thread-clear');
  const status = document.getElementById('thread-status');
  const origin = document.getElementById('thread-origin');
  const cards = document.getElementById('thread-leads');
  const trail = document.getElementById('thread-trail');
  const normalize = text => text.normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  let data, selected, activeLead;
  const element = (tag, text, className) => {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = text;
    if (className) node.className = className;
    return node;
  };
  function updateURL() {
    const url = new URL(location.href);
    selected ? url.searchParams.set('start', selected.title) : url.searchParams.delete('start');
    activeLead ? url.searchParams.set('lead', activeLead.id) : url.searchParams.delete('lead');
    // Preserve cache version and other parameters; the link can be shared.
    history.replaceState(null, '', url);
  }
  function available() {
    return data.leads.filter(lead => lead.steps.slice(0, -1).some(step => step.title === selected.title));
  }
  function remaining(lead) {
    return lead.steps.slice(lead.steps.findIndex(step => step.title === selected.title));
  }
  function showOptions() {
    if (!data) return;
    options.replaceChildren();
    const tokens = normalize(query.value).trim().split(/\s+/).filter(Boolean);
    const matches = data.starts.filter(note => tokens.every(token => normalize([note.title, note.summary, note.text, ...note.tags].join(' ')).includes(token)))
      .sort((a,b) => Number(normalize(b.title).includes(normalize(query.value))) - Number(normalize(a.title).includes(normalize(query.value))));
    status.textContent = matches.length ? (tokens.length ? `${matches.length} starting note${matches.length === 1 ? '' : 's'}. Choose one below.` : 'Choose a starting note, or search its ideas and reading guide.') : 'No matching published notes yet. Try another word.';
    for (const note of matches) {
      const item = element('li');
      const button = element('button'); button.type = 'button';
      button.append(element('strong', note.title), element('small', note.category));
      button.addEventListener('click', () => choose(note));
      item.append(button); options.append(item);
    }
  }
  function showLeads() {
    cards.replaceChildren(); trail.replaceChildren(); trail.hidden = true;
    activeLead = null;
    const leads = available();
    cards.append(element('h3', 'Where do you want to go next?'));
    if (!leads.length) {
      cards.append(element('p', 'There are no curated leads from this note yet. Choose another starting note.', 'muted'));
      return;
    }
    const grid = element('div', undefined, 'lead-grid');
    leads.forEach((lead, index) => {
      const steps = remaining(lead);
      const published = steps.filter(step => step.status === 'Handwritten note').length;
      const planned = steps.length - published;
      const button = element('button', undefined, 'lead-card'); button.type = 'button';
      button.append(element('small', String(index + 1).padStart(2,'0'), 'lead-number'), element('strong', lead.question),
        element('span', `${published} handwritten ${published === 1 ? 'note' : 'notes'}${planned ? ` · ${planned} planned ${planned === 1 ? 'step' : 'steps'}` : ''}`, 'lead-count'),
        element('span', steps.map(step => step.title).join(' → '), 'lead-path'), element('span', 'Follow this question →', 'lead-action'));
      button.addEventListener('click', () => showTrail(lead, true));
      grid.append(button);
    });
    cards.append(grid);
  }
  function showTrail(lead, moveFocus = false) {
    activeLead = lead; cards.hidden = true; trail.hidden = false; trail.replaceChildren();
    const back = element('button', '← Other questions', 'thread-back'); back.type = 'button';
    back.addEventListener('click', () => {cards.hidden = false; showLeads(); updateURL(); cards.querySelector('button')?.focus();});
    const heading = element('h3', lead.question); heading.tabIndex = -1;
    trail.append(back, heading);
    const list = element('ol', undefined, 'trail-steps');
    const steps = remaining(lead);
    steps.forEach((step, i) => {
      const item = element('li');
      const link = element('a', step.title); link.href = step.url;
      item.append(element('small', i === 0 ? 'You are here' : `Step ${String(i).padStart(2,'0')}`), link,
        element('span', step.status === 'Handwritten note' ? 'Handwritten note' : 'Planned chapter · outline', 'trail-status'));
      list.append(item);
    });
    trail.append(list);
    const next = steps[1];
    const begin = element('a', next.status === 'Handwritten note' ? `Begin with ${next.title} →` : `Explore ${next.title} outline →`, 'button');
    begin.href = next.url;
    trail.append(begin);
    if (next.status !== 'Handwritten note') trail.append(element('p', 'This step’s handwritten chapter is still to come. You can explore its outline or open any published note along the trail.', 'muted'));
    const openStart = element('a', 'Read the starting note ↗', 'section-link'); openStart.href = selected.url;
    const startLink = element('p'); startLink.append(openStart); trail.append(startLink);
    updateURL(); if (moveFocus) heading.focus({preventScroll:true});
  }
  function choose(note, requestedLead) {
    selected = note; query.value = note.title; options.replaceChildren(); clear.hidden = false;
    status.textContent = 'Starting note selected. Choose a question below, or search for another note.';
    origin.hidden = false; origin.replaceChildren(element('p', 'You are here', 'kicker'), element('h3', note.title), element('p', note.summary, 'muted'));
    cards.hidden = false; showLeads();
    const lead = available().find(lead => lead.id === requestedLead);
    if (lead) showTrail(lead); else updateURL();
  }
  function reset() {
    selected = null; activeLead = null; clear.hidden = true;
    origin.hidden = true; cards.replaceChildren(); cards.hidden = false; trail.hidden = true;
    showOptions(); updateURL();
  }
  clear.addEventListener('click', () => {query.value = ''; reset(); query.focus();});
  query.addEventListener('input', reset);
  query.addEventListener('keydown', event => {
    if (event.key === 'ArrowDown' && options.querySelector('button')) {event.preventDefault(); options.querySelector('button').focus();}
    if (event.key === 'Enter' && options.querySelector('button')) {event.preventDefault(); options.querySelector('button').click();}
  });
  options.addEventListener('keydown', event => {
    if (!['ArrowDown','ArrowUp','Escape'].includes(event.key)) return;
    event.preventDefault();
    const buttons = [...options.querySelectorAll('button')]; const index = buttons.indexOf(document.activeElement);
    if (event.key === 'Escape' || (event.key === 'ArrowUp' && index <= 0)) query.focus();
    else buttons[Math.max(0, Math.min(buttons.length-1, index + (event.key === 'ArrowDown' ? 1 : -1)))]?.focus();
  });
  fetch(new URL('../leads-index.json', script.src), {cache:'no-store'}).then(response => {
    if (!response.ok) throw new Error('Leads unavailable'); return response.json();
  }).then(value => {
    data = value;
    const params = new URL(location.href).searchParams;
    const note = data.starts.find(note => note.title === params.get('start'));
    note ? choose(note, params.get('lead')) : showOptions();
  }).catch(() => {status.textContent = 'The explorer could not load. You can still browse Notes and follow leads from any chapter.';});
})();
