(() => {
  const root = document.documentElement;
  const forced = new URL(location.href).searchParams.get('theme');
  let saved;
  try { saved = localStorage.getItem('notebook-theme'); } catch (_) {}
  const initial = ['dark', 'light'].includes(forced) ? forced : saved === 'dark' ? 'dark' : 'light';
  root.dataset.theme = initial;
  function apply(theme) {
    root.dataset.theme = theme;
    const button = document.querySelector('[data-theme-toggle]');
    if (button) {
      button.textContent = theme === 'dark' ? 'Light' : 'Dark';
      button.setAttribute('aria-label', `Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`);
    }
  }
  document.addEventListener('DOMContentLoaded', () => {
    apply(initial);
    document.querySelector('[data-theme-toggle]')?.addEventListener('click', () => {
      const theme = root.dataset.theme === 'dark' ? 'light' : 'dark';
      apply(theme);
      try { localStorage.setItem('notebook-theme', theme); } catch (_) {}
      const url = new URL(location.href);
      if (url.searchParams.has('theme')) {url.searchParams.set('theme', theme); history.replaceState(null, '', url);}
    });
  });
})();
