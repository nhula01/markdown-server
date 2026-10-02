(async () => {
  const root = document.querySelector('[data-margin-equations]');
  if (!root || !window.katex) return;
  const source = new URL('margin-reminders.json',document.currentScript.src);
  let equations;
  try {
    const response = await fetch(source,{cache:'no-store'});
    if (!response.ok) return;
    equations = await response.json();
    equations.forEach(item=>katex.renderToString(item.tex,{throwOnError:true,trust:false}));
  } catch {return;}
  if (!equations.length || !root.isConnected) return;
  const slots = [...root.querySelectorAll('.margin-equation')];
  const wide = window.matchMedia('(min-width:1200px)');
  const tall = window.matchMedia('(min-height:750px)');
  const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
  let timers = [], index = 0;
  function reveal(slot) {
    slot.classList.remove('equation-visible');
    const {label,tex,intuition} = equations[index];
    slot.querySelector('.margin-equation-label').textContent = label;
    slot.querySelector('.margin-equation-intuition').textContent = intuition;
    const math = slot.querySelector('.margin-equation-math');
    math.style.fontSize = '';
    katex.render(tex,math,{throwOnError:true,trust:false,displayMode:true});
    const width = math.querySelector('.katex-html').getBoundingClientRect().width;
    const available = slot.getBoundingClientRect().width;
    if(width > available) math.style.fontSize = `${parseFloat(getComputedStyle(math).fontSize) * available / width * .95}px`;
    void slot.offsetWidth;
    slot.classList.add('equation-visible');
    index = (index + 1) % equations.length;
  }
  function schedule() {
    timers.forEach(timer=>{clearTimeout(timer);clearInterval(timer);}); timers = [];
    slots.forEach(slot=>slot.classList.remove('equation-visible'));
    if (!wide.matches || motion.matches || document.hidden || document.body.classList.contains('ink-immersive')) return;
    const active = tall.matches ? slots : slots.slice(0,2);
    active.forEach((slot,i)=>{
      const start = ()=>{reveal(slot);timers.push(setInterval(()=>reveal(slot),44000));};
      if(i===0) start(); else timers.push(setTimeout(start,i*6000));
    });
  }
  [wide,tall,motion].forEach(query=>query.addEventListener('change',schedule));
  document.addEventListener('visibilitychange',schedule);
  new MutationObserver(schedule).observe(document.body,{attributes:true,attributeFilter:['class']});
  schedule();
})();
