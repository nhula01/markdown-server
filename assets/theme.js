(() => {
  const root = document.documentElement;
  const themes = ['light', 'dark'];
  const forced = new URL(location.href).searchParams.get('theme');
  let saved;
  try {saved = localStorage.getItem('notebook-theme');} catch (_) {}
  // Retired Wuxia preferences migrate to the familiar Dark appearance.
  const requested = forced === 'wuxia' ? 'dark' : forced;
  const stored = saved === 'wuxia' ? 'dark' : saved;
  const initial = themes.includes(requested) ? requested : themes.includes(stored) ? stored : 'light';
  root.dataset.theme = initial;
  if (themes.includes(requested) || saved === 'wuxia') {try {localStorage.setItem('notebook-theme', initial);} catch (_) {}}
  function apply(theme) {
    root.dataset.theme = theme;
    const button = document.querySelector('[data-theme-toggle]');
    if (button) {
      const label = theme === 'light' ? 'Switch to dark mode' : 'Switch to light mode';
      button.setAttribute('aria-label',label);
      button.title = label;
      button.setAttribute('aria-pressed',String(theme === 'light'));
    }
  }
  document.addEventListener('DOMContentLoaded', () => {
    apply(initial);
    document.querySelector('[data-theme-toggle]')?.addEventListener('click', () => {
      const theme = root.dataset.theme === 'light' ? 'dark' : 'light';
      apply(theme);
      try {localStorage.setItem('notebook-theme', theme);} catch (_) {}
      const url = new URL(location.href);
      if (url.searchParams.has('theme')) {url.searchParams.set('theme', theme); history.replaceState(null, '', url);}
    });
  });
})();
