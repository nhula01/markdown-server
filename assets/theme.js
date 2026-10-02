(() => {
  const root = document.documentElement;
  const themes = ['light', 'dark', 'wuxia'];
  const forced = new URL(location.href).searchParams.get('theme');
  let saved;
  try {saved = localStorage.getItem('notebook-theme');} catch (_) {}
  const initial = themes.includes(forced) ? forced : themes.includes(saved) ? saved : 'light';
  root.dataset.theme = initial;
  if (themes.includes(forced)) {try {localStorage.setItem('notebook-theme', initial);} catch (_) {}}
  function apply(theme) {
    root.dataset.theme = theme;
    const picker = document.querySelector('[data-theme-select]');
    if (picker) picker.value = theme;
  }
  document.addEventListener('DOMContentLoaded', () => {
    apply(initial);
    document.querySelector('[data-theme-select]')?.addEventListener('change', event => {
      const theme = event.target.value;
      if (!themes.includes(theme)) return;
      apply(theme);
      try {localStorage.setItem('notebook-theme', theme);} catch (_) {}
      const url = new URL(location.href);
      if (url.searchParams.has('theme')) {url.searchParams.set('theme', theme); history.replaceState(null, '', url);}
    });
  });
})();
