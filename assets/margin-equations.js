(() => {
  const root = document.querySelector('[data-margin-equations]');
  if (!root || !window.katex) return;
  const equations = [
    ['Light in vacuum',String.raw`c = \frac{1}{\sqrt{\varepsilon_0\mu_0}}`],
    ['Photon energy',String.raw`E = \hbar\omega`],
    ['Faraday’s law',String.raw`\nabla\!\times\!\mathbf{E} = -\partial_t\mathbf{B}`],
    ['Uncertainty',String.raw`\Delta x\,\Delta p \geq \frac{\hbar}{2}`],
    ['Quantum dynamics',String.raw`i\hbar\partial_t\psi = \hat H\psi`],
    ['Magnetic flux',String.raw`\nabla\!\cdot\!\mathbf{B}=0`],
    ['Photon momentum',String.raw`p=\hbar k`],
    ['Canonical pair',String.raw`[\hat x,\hat p]=i\hbar`],
    ['A harmonic mode',String.raw`E_n=\hbar\omega(n+\tfrac12)`],
    ['Probability',String.raw`\operatorname{Tr}\rho=1`]
  ];
  const slots = [...root.querySelectorAll('.margin-equation')];
  const wide = window.matchMedia('(min-width:1540px)');
  const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
  let timer, index = 0, side = 0;
  function reveal() {
    const slot = slots[side];
    slot.classList.remove('equation-visible');
    const [label,tex] = equations[index];
    slot.querySelector('.margin-equation-label').textContent = label;
    const math = slot.querySelector('.margin-equation-math');
    math.style.fontSize = '';
    katex.render(tex,math,{throwOnError:true,trust:false,displayMode:true});
    const width = math.querySelector('.katex-html').getBoundingClientRect().width;
    const available = slot.getBoundingClientRect().width;
    if(width > available) math.style.fontSize = `${parseFloat(getComputedStyle(math).fontSize) * available / width * .95}px`;
    // Restart the fade only for this margin, without moving the page.
    void slot.offsetWidth;
    slot.classList.add('equation-visible');
    index = (index + 1) % equations.length;
    side = 1 - side;
  }
  function schedule() {
    clearInterval(timer);
    slots.forEach(slot=>slot.classList.remove('equation-visible'));
    if (!wide.matches || motion.matches || document.hidden || document.body.classList.contains('ink-immersive')) return;
    reveal(); timer = setInterval(reveal,12000);
  }
  wide.addEventListener('change',schedule);
  motion.addEventListener('change',schedule);
  document.addEventListener('visibilitychange',schedule);
  new MutationObserver(schedule).observe(document.body,{attributes:true,attributeFilter:['class']});
  schedule();
})();
