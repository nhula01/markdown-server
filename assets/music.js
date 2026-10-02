(() => {
  const player = document.querySelector('[data-reading-music]');
  if (!player) return;
  const source = new URL('audio/gymnopedie-no-1.mp3',document.currentScript.src).href;
  const audio = player.querySelector('audio'), button = player.querySelector('[data-music-play]');
  const status = player.querySelector('[data-music-status]');
  const icon = player.querySelector('[data-music-icon]');
  let context, gain, analyser, samples, frame, energy = 0, loading = false;
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  function animate() {
    frame = null;
    if (audio.paused || reducedMotion.matches || !analyser || document.hidden) return;
    analyser.getByteTimeDomainData(samples);
    let sum = 0;
    for (const sample of samples) sum += ((sample - 128) / 128) ** 2;
    const level = Math.min(1,Math.sqrt(sum / samples.length) * 22);
    energy += (level - energy) * 0.18;
    button.style.setProperty('--music-scale',String(1 + energy * 0.18));
    button.style.setProperty('--music-halo',`${2 + energy * 9}px`);
    frame = requestAnimationFrame(animate);
  }
  function resetPulse() {
    cancelAnimationFrame(frame); frame = null; energy = 0;
    button.style.removeProperty('--music-scale');
    button.style.removeProperty('--music-halo');
  }
  function syncPulse() {
    resetPulse();
    if (!audio.paused && !reducedMotion.matches && !document.hidden) animate();
  }
  function update() {
    const label = audio.paused ? 'Play music' : 'Pause music';
    button.setAttribute('aria-label',label);
    button.title = `${label} · Satie: Gymnopédie No. 1`;
    icon.textContent = audio.paused ? '▶' : 'Ⅱ';
    syncPulse();
    button.setAttribute('aria-pressed',String(!audio.paused));
  }
  function setVolume() {
    const level = 0.2;
    if (gain) gain.gain.setValueAtTime(level,context.currentTime);
    else audio.volume = level;
  }
  button.addEventListener('click',async()=>{
    if (loading) return;
    if (!audio.paused) {audio.pause(); return;}
    loading = true; button.disabled = true;
    status.textContent = 'Loading music…';
    try {
      if (!audio.src) audio.src = source;
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      if (!context && AudioContextClass) {
        context = new AudioContextClass();
        gain = context.createGain();
        analyser = context.createAnalyser(); analyser.fftSize = 512;
        samples = new Uint8Array(analyser.fftSize);
        context.createMediaElementSource(audio).connect(analyser);
        analyser.connect(gain); gain.connect(context.destination);
        audio.volume = 1;
      }
      setVolume();
      // Both calls start inside the reader's click, preserving mobile activation.
      await Promise.all([context ? context.resume() : Promise.resolve(),audio.play()]);
      status.textContent = 'Playing · repeats gently';
    } catch {
      audio.pause(); status.textContent = 'Music could not play. Press Play to try again.';
    } finally {loading = false; button.disabled = false; update();}
  });
  audio.addEventListener('play',update);
  audio.addEventListener('pause',()=>{update(); if(!loading) status.textContent = 'Paused';});
  audio.addEventListener('error',()=>{status.textContent = 'Music is unavailable. Please try again later.';update();});
  document.addEventListener('visibilitychange',syncPulse);
  reducedMotion.addEventListener('change',syncPulse);
  setVolume(); update();
})();
