(() => {
  const player = document.querySelector('[data-reading-music]');
  if (!player) return;
  // The outer page owns playback; reading pages navigate normally inside it.
  if (window !== window.top) {player.remove(); return;}
  const assetBase = new URL('audio/',document.currentScript.src);
  const tracks = [
    ['Satie · Gymnopédie No. 1','gymnopedie-no-1.mp3'],
    ['Beethoven · Moonlight Sonata, I','moonlight-adagio.mp3'],
    ['Chopin · Prelude Op. 28 No. 17','chopin-prelude-17.mp3']
  ];
  const audio = player.querySelector('audio'), button = player.querySelector('[data-music-play]');
  const status = player.querySelector('[data-music-status]'), icon = player.querySelector('[data-music-icon]');
  const next = player.querySelector('[data-music-next]');
  let context, gain, loading = false, track = 0, frame;
  audio.loop = false;
  function update() {
    const label = audio.paused ? 'Play music' : 'Pause music';
    button.setAttribute('aria-label',label);
    button.title = `${label} · ${tracks[track][0]}`;
    icon.textContent = audio.paused ? '▶' : 'Ⅱ';
    button.setAttribute('aria-pressed',String(!audio.paused));
    next.title = `Next song · ${tracks[(track + 1) % tracks.length][0]}`;
  }
  function keepReading(url) {
    if (frame) return;
    history.pushState(null,'',url);
    frame = document.createElement('iframe');
    frame.className = 'music-reading-frame';
    frame.title = 'Notebook';
    let first = true, observer;
    frame.addEventListener('load',()=>{
      try {
        const win = frame.contentWindow, doc = frame.contentDocument;
        document.title = doc.title;
        if (win.location.origin === location.origin) history.replaceState(null,'',win.location.href);
        document.documentElement.dataset.theme = doc.documentElement.dataset.theme;
        observer?.disconnect();
        observer = new MutationObserver(()=>{document.documentElement.dataset.theme = doc.documentElement.dataset.theme;});
        observer.observe(doc.documentElement,{attributes:true,attributeFilter:['data-theme']});
        doc.querySelectorAll('a[href]').forEach(link=>{
          if (link.origin !== location.origin) {link.target = '_blank'; link.rel = 'noopener';}
        });
        if (first) {
          first = false;
          win.focus();
        }
      } catch { /* External downloads do not affect the music. */ }
    });
    frame.src = url;
    document.body.append(frame);
    document.body.classList.remove('ink-immersive');
    document.body.classList.add('music-reading-shell');
    next.hidden = false;
  }
  async function play() {
    if (loading) return;
    loading = true; button.disabled = true;
    status.textContent = 'Loading music…';
    try {
      if (!audio.src) audio.src = new URL(tracks[track][1],assetBase).href;
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      if (!context && AudioContextClass) {
        context = new AudioContextClass(); gain = context.createGain();
        context.createMediaElementSource(audio).connect(gain); gain.connect(context.destination);
        audio.volume = 1; gain.gain.setValueAtTime(0.2,context.currentTime);
      } else if (!context) audio.volume = 0.2;
      await Promise.all([context ? context.resume() : Promise.resolve(),audio.play()]);
      status.textContent = `Playing · ${tracks[track][0]}`;
      next.hidden = false;
    } catch {audio.pause(); status.textContent = 'Music could not play. Press Play to try again.';}
    finally {loading = false; button.disabled = false; update();}
  }
  async function advance() {
    if (loading) return;
    const shouldPlay = !audio.paused || audio.ended;
    track = (track + 1) % tracks.length;
    audio.src = new URL(tracks[track][1],assetBase).href;
    update();
    if (shouldPlay) await play();
  }
  // Start the persistent reading frame on the first actual section change,
  // preserving any review answers or PDF settings on the current page.
  document.addEventListener('click',event=>{
    if (!audio.src || frame || event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    const link = event.target.closest('a[href]');
    if (!link || link.target || link.hasAttribute('download')) return;
    const url = new URL(link.href);
    if (url.origin !== location.origin || url.pathname === location.pathname && url.search === location.search) return;
    if (!url.pathname.endsWith('/')) return;
    event.preventDefault(); keepReading(url.href);
  });
  window.addEventListener('popstate',()=>{
    if (!frame) return;
    try {if(frame.contentWindow.location.href !== location.href) frame.contentWindow.location.replace(location.href);} catch {}
  });
  button.addEventListener('click',()=>{if(loading)return; if(!audio.paused)audio.pause(); else play();});
  next.addEventListener('click',advance);
  audio.addEventListener('ended',advance);
  audio.addEventListener('play',update);
  audio.addEventListener('pause',()=>{update();if(!loading)status.textContent = 'Paused';});
  audio.addEventListener('error',()=>{status.textContent = 'Music is unavailable. Please try again later.';update();});
  update();
})();
