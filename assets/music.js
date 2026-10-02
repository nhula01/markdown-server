(() => {
  const player = document.querySelector('[data-reading-music]');
  if (!player) return;
  const source = new URL('audio/gymnopedie-no-1.mp3',document.currentScript.src).href;
  const audio = player.querySelector('audio'), button = player.querySelector('[data-music-play]');
  const volume = player.querySelector('[data-music-volume]'), status = player.querySelector('[data-music-status]');
  let context, gain, loading = false;
  function update() {
    button.textContent = audio.paused ? 'Play music' : 'Pause music';
    button.setAttribute('aria-pressed',String(!audio.paused));
  }
  function setVolume() {
    const level = Number(volume.value)/100;
    if (gain) gain.gain.setValueAtTime(level,context.currentTime);
    else audio.volume = level;
    volume.setAttribute('aria-valuetext',`${volume.value}%`);
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
        context.createMediaElementSource(audio).connect(gain); gain.connect(context.destination);
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
  volume.addEventListener('input',setVolume);
  audio.addEventListener('play',update);
  audio.addEventListener('pause',()=>{update(); if(!loading) status.textContent = 'Paused';});
  audio.addEventListener('error',()=>{status.textContent = 'Music is unavailable. Please try again later.';update();});
  setVolume(); update();
})();
