import * as pdfjs from './vendor/pdfjs-6.3.289/build/pdf.min.mjs';

const reader = document.querySelector('.pdf-reader');
const vendor = new URL('./vendor/pdfjs-6.3.289/', import.meta.url);
pdfjs.GlobalWorkerOptions.workerSrc = new URL('build/pdf.worker.min.mjs', vendor).href;
const canvas = reader.querySelector('canvas');
const surface = reader.querySelector('.pdf-surface');
const depthStage = document.createElement('div'); depthStage.className = 'ink-depth-stage';
canvas.before(depthStage);
const depthShadow = document.createElement('canvas'); depthShadow.className = 'ink-depth-shadow'; depthShadow.setAttribute('aria-hidden', 'true');
const depthEdge = document.createElement('canvas'); depthEdge.className = 'ink-depth-edge'; depthEdge.setAttribute('aria-hidden', 'true');
canvas.classList.add('ink-source');
const amplifiedCanvas = document.createElement('canvas'); amplifiedCanvas.className = 'ink-amplified';
amplifiedCanvas.hidden = true;
depthStage.append(depthShadow, depthEdge, canvas, amplifiedCanvas);
const status = reader.querySelector('[data-pdf-status]');
const selector = reader.querySelector('[data-pdf-select]');
const previous = reader.querySelector('[data-pdf-previous]');
const next = reader.querySelector('[data-pdf-next]');
const zoomOut = reader.querySelector('[data-pdf-zoom-out]');
const zoomIn = reader.querySelector('[data-pdf-zoom-in]');
// Display-only cutout. Re-rendering restores the complete original page.
let immersive = false, previousFloating;
const floatingParam = new URL(location.href).searchParams.get('floating');
let floatingChosen = floatingParam !== null;
let floating = floatingParam === '1' || (floatingParam === null && document.documentElement.dataset.theme === 'wuxia');
const floatingToggle = document.createElement('button');
floatingToggle.type = 'button'; floatingToggle.className = 'pdf-floating-toggle';
floatingToggle.textContent = 'Floating ink'; floatingToggle.disabled = true;
floatingToggle.setAttribute('aria-pressed', String(floating));
floatingToggle.setAttribute('aria-label', 'Floating ink view');
reader.dataset.floating = String(floating);
const immersiveToggle = document.createElement('button');
immersiveToggle.type = 'button'; immersiveToggle.className = 'pdf-immersive-toggle';
immersiveToggle.textContent = 'Immersive view'; immersiveToggle.disabled = true;
immersiveToggle.setAttribute('aria-pressed', 'false');
const depthToggle = document.createElement('button'); depthToggle.type = 'button';
depthToggle.textContent = '3D depth'; depthToggle.setAttribute('aria-pressed', 'true'); depthToggle.hidden = true;
let depthEnabled = true;
reader.dataset.depth = 'true';
depthToggle.addEventListener('click', () => {
  depthEnabled = !depthEnabled; reader.dataset.depth = String(depthEnabled);
  depthToggle.setAttribute('aria-pressed', String(depthEnabled));
});
const shadeToggle = document.createElement('button'); shadeToggle.type = 'button';
shadeToggle.textContent = 'Floating shadow'; shadeToggle.hidden = true;
shadeToggle.setAttribute('aria-pressed', 'true'); reader.dataset.shading = 'true';
shadeToggle.addEventListener('click', () => {
  const enabled = reader.dataset.shading !== 'true';
  reader.dataset.shading = String(enabled); shadeToggle.setAttribute('aria-pressed', String(enabled));
});
const amplifyToggle = document.createElement('button'); amplifyToggle.type = 'button';
amplifyToggle.textContent = 'Pointer emphasis'; amplifyToggle.hidden = true;
amplifyToggle.setAttribute('aria-pressed', 'true');
let amplifyEnabled = true, sourceFrame, dirtyRegion, lensFrame;
function hideAmplification() {
  cancelAnimationFrame(lensFrame);
  amplifiedCanvas.hidden = true; reader.dataset.amplified = 'false';
}
amplifyToggle.addEventListener('click', () => {
  amplifyEnabled = !amplifyEnabled; amplifyToggle.setAttribute('aria-pressed', String(amplifyEnabled)); hideAmplification();
});
reader.querySelector('.pdf-controls').append(floatingToggle, depthToggle, shadeToggle, amplifyToggle, immersiveToggle);
// A continuous local deformation of the same ink plane. The displacement
// smoothly reaches zero at its edge, so there is no lens, seam, or duplicate.
function emphasizeInk(clientX, clientY) {
  const bounds = canvas.getBoundingClientRect();
  if (!sourceFrame || clientX < bounds.left || clientX > bounds.right || clientY < bounds.top || clientY > bounds.bottom) {hideAmplification(); return;}
  const width = canvas.width, height = canvas.height;
  const cx = (clientX - bounds.left) / bounds.width * width;
  const cy = (clientY - bounds.top) / bounds.height * height;
  const scaleX = width / bounds.width, scaleY = height / bounds.height, radius = 150;
  const left = Math.max(0, Math.floor(cx - radius * scaleX));
  const top = Math.max(0, Math.floor(cy - radius * scaleY));
  const right = Math.min(width, Math.ceil(cx + radius * scaleX));
  const bottom = Math.min(height, Math.ceil(cy + radius * scaleY));
  const context = amplifiedCanvas.getContext('2d');
  if (dirtyRegion) context.putImageData(sourceFrame, 0, 0, ...dirtyRegion);
  const patch = context.createImageData(right - left, bottom - top), original = sourceFrame.data;
  for (let y = top; y < bottom; y++) for (let x = left; x < right; x++) {
    const dx = x - cx, dy = y - cy;
    const r2 = (dx / scaleX) ** 2 + (dy / scaleY) ** 2;
    const falloff = Math.max(0, 1 - r2 / (radius * radius));
    const contraction = 1 - .13 * falloff ** 3;
    const sx = Math.max(0, Math.min(width - 1, cx + dx * contraction));
    const sy = Math.max(0, Math.min(height - 1, cy + dy * contraction));
    const x0 = Math.floor(sx), y0 = Math.floor(sy), fx = sx - x0, fy = sy - y0;
    const indices = [(y0 * width + x0) * 4, (y0 * width + Math.min(width - 1, x0 + 1)) * 4,
      (Math.min(height - 1, y0 + 1) * width + x0) * 4,
      (Math.min(height - 1, y0 + 1) * width + Math.min(width - 1, x0 + 1)) * 4];
    const weights = [(1-fx)*(1-fy), fx*(1-fy), (1-fx)*fy, fx*fy];
    let alpha = 0, red = 0, green = 0, blue = 0;
    for (let n = 0; n < 4; n++) {
      const index = indices[n], weight = weights[n] * original[index + 3];
      alpha += weight; red += original[index] * weight; green += original[index+1] * weight; blue += original[index+2] * weight;
    }
    const dest = ((y - top) * patch.width + x - left) * 4;
    if (alpha) {patch.data[dest] = red / alpha; patch.data[dest+1] = green / alpha; patch.data[dest+2] = blue / alpha;}
    patch.data[dest+3] = alpha;
  }
  context.putImageData(patch, left, top);
  dirtyRegion = [left, top, patch.width, patch.height];
  amplifiedCanvas.hidden = false; reader.dataset.amplified = 'true';
}
surface.addEventListener('pointermove', event => {
  if (!immersive || !amplifyEnabled || event.pointerType === 'touch') return;
  cancelAnimationFrame(lensFrame);
  lensFrame = requestAnimationFrame(() => emphasizeInk(event.clientX, event.clientY));
});
surface.addEventListener('scroll', hideAmplification);
const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
surface.addEventListener('pointermove', event => {
  if (!immersive || !depthEnabled || reduceMotion.matches || event.pointerType === 'touch') return;
  const bounds = surface.getBoundingClientRect();
  const x = Math.max(-1, Math.min(1, (event.clientX - bounds.left) / bounds.width * 2 - 1));
  const y = Math.max(-1, Math.min(1, (event.clientY - bounds.top) / bounds.height * 2 - 1));
  depthStage.style.setProperty('--ink-tilt-x', `${5 - y * 3}deg`);
  depthStage.style.setProperty('--ink-tilt-y', `${-7 + x * 4}deg`);
});
surface.addEventListener('pointerleave', () => {
  hideAmplification();
  depthStage.style.removeProperty('--ink-tilt-x'); depthStage.style.removeProperty('--ink-tilt-y');
});
function setImmersive(enabled) {
  immersive = enabled;
  depthToggle.hidden = !enabled; shadeToggle.hidden = !enabled; amplifyToggle.hidden = !enabled;
  hideAmplification();
  if (enabled) {previousFloating = floating; floating = true;}
  else floating = previousFloating;
  floatingToggle.setAttribute('aria-pressed', String(floating));
  immersiveToggle.setAttribute('aria-pressed', String(enabled));
  immersiveToggle.textContent = enabled ? 'Exit immersive · Esc' : 'Immersive view';
  reader.dataset.immersive = String(enabled);
  document.body.classList.toggle('ink-immersive', enabled);
  if (enabled) {reader.setAttribute('role', 'dialog'); reader.setAttribute('aria-modal', 'true'); reader.setAttribute('aria-label', 'Immersive handwritten notes');}
  else {reader.removeAttribute('role'); reader.removeAttribute('aria-modal'); reader.removeAttribute('aria-label');}
  if (documentPDF) render(requestedPage);
  immersiveToggle.focus({preventScroll: true});
}
immersiveToggle.addEventListener('click', () => setImmersive(!immersive));
reader.addEventListener('keydown', event => {
  if (!immersive || event.key !== 'Tab') return;
  const controls = [...reader.querySelectorAll('button:not(:disabled), select:not(:disabled)')];
  if (event.shiftKey && document.activeElement === controls[0]) {event.preventDefault(); controls.at(-1).focus();}
  else if (!event.shiftKey && document.activeElement === controls.at(-1)) {event.preventDefault(); controls[0].focus();}
});
document.addEventListener('keydown', event => {if (event.key === 'Escape' && immersive) {event.preventDefault(); setImmersive(false);}});

function extractInk() {
  const context = canvas.getContext('2d');
  const frame = context.getImageData(0, 0, canvas.width, canvas.height);
  const pixels = frame.data;
  for (let i = 0; i < pixels.length; i += 4) {
    const r = pixels[i], g = pixels[i + 1], b = pixels[i + 2];
    const low = Math.min(r, g, b), high = Math.max(r, g, b);
    const luminance = .2126*r + .7152*g + .0722*b;
    // Keep colored marks; suppress white paper and the faint neutral template grid.
    const colored = high - low > 35;
    const opacity = colored ? 1 - low / 255 : Math.max(0, Math.min(1, (160 - luminance) / 85));
    pixels[i + 3] = Math.round(pixels[i + 3] * opacity);
    if (colored && opacity > 0) {
      // Remove the white paper matte from antialiased colored strokes.
      // This retains hue instead of tinting every mark gold or inverting it.
      pixels[i] = Math.max(0, Math.round((r - 255 * (1 - opacity)) / opacity));
      pixels[i + 1] = Math.max(0, Math.round((g - 255 * (1 - opacity)) / opacity));
      pixels[i + 2] = Math.max(0, Math.round((b - 255 * (1 - opacity)) / opacity));
    } else if (immersive || document.documentElement.dataset.theme !== 'light') {
      pixels[i] = pixels[i + 1] = pixels[i + 2] = 255;
    }
  }
  context.putImageData(frame, 0, 0);
  for (const layer of [depthShadow, depthEdge]) {
    layer.width = canvas.width; layer.height = canvas.height;
    layer.style.width = canvas.style.width; layer.style.height = canvas.style.height;
  }
  if (immersive) {
    // The very same transparent strokes form three physically separated planes.
    for (let i = 0; i < pixels.length; i += 4) {pixels[i] *= .35; pixels[i+1] *= .35; pixels[i+2] *= .35;}
    depthEdge.getContext('2d').putImageData(frame, 0, 0);
    for (let i = 0; i < pixels.length; i += 4) {pixels[i] = 0; pixels[i+1] = 0; pixels[i+2] = 0;}
    depthShadow.getContext('2d').putImageData(frame, 0, 0);
  }
}
let documentPDF, requestedPage = Number(reader.dataset.page || 1), zoom = 1, revision = 0, renderTask;

async function render(number) {
  requestedPage = Math.max(1, Math.min(number, documentPDF.numPages));
  const ticket = ++revision;
  hideAmplification(); sourceFrame = null;
  status.textContent = `Loading page ${requestedPage}…`;
  try {
    if (renderTask) {renderTask.cancel(); await renderTask.promise.catch(() => {});}
    const page = await documentPDF.getPage(requestedPage);
    if (ticket !== revision) return;
    const surfaceStyle = getComputedStyle(surface);
    const availableWidth = surface.clientWidth - parseFloat(surfaceStyle.paddingLeft) - parseFloat(surfaceStyle.paddingRight) - 2;
    const fit = availableWidth / page.getViewport({scale: 1}).width;
    const viewport = page.getViewport({scale: fit * zoom});
    const density = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.ceil(viewport.width * density);
    canvas.height = Math.ceil(viewport.height * density);
    canvas.style.width = `${viewport.width}px`;
    canvas.style.height = `${viewport.height}px`;
    depthStage.style.width = canvas.style.width;
    depthStage.style.height = canvas.style.height;
    canvas.setAttribute('aria-label', `${reader.dataset.title}, handwritten page ${requestedPage} of ${documentPDF.numPages}`);
    amplifiedCanvas.setAttribute('aria-label', canvas.getAttribute('aria-label'));
    renderTask = page.render({canvasContext: canvas.getContext('2d'), viewport,
      transform: [density, 0, 0, density, 0, 0]});
    await renderTask.promise;
    if (ticket !== revision) return;
    if (floating) extractInk();
    if (immersive) {
      sourceFrame = canvas.getContext('2d').getImageData(0, 0, canvas.width, canvas.height);
      amplifiedCanvas.width = canvas.width; amplifiedCanvas.height = canvas.height;
      amplifiedCanvas.style.width = canvas.style.width; amplifiedCanvas.style.height = canvas.style.height;
      amplifiedCanvas.getContext('2d').putImageData(sourceFrame, 0, 0); dirtyRegion = null;
    }
    reader.dataset.floating = String(floating);
    floatingToggle.disabled = immersive;
    immersiveToggle.disabled = false;
    reader.dataset.page = String(requestedPage);
    selector.value = String(requestedPage);
    previous.disabled = requestedPage === 1;
    next.disabled = requestedPage === documentPDF.numPages;
    zoomOut.disabled = zoom <= 1;
    zoomIn.disabled = zoom >= 2.5;
    status.textContent = `Page ${requestedPage} of ${documentPDF.numPages} · ${Math.round(zoom * 100)}% of page width`;
    document.querySelectorAll('[data-pdf-page]').forEach(link => {
      if (Number(link.dataset.pdfPage) === requestedPage) link.setAttribute('aria-current', 'true');
      else link.removeAttribute('aria-current');
    });
  } catch (error) {
    if (error.name !== 'RenderingCancelledException' && ticket === revision) {
      status.textContent = 'This page could not display. Use Open PDF to read the original.';
    }
  }
}

floatingToggle.addEventListener('click', () => {
  floatingChosen = true;
  floating = !floating;
  floatingToggle.setAttribute('aria-pressed', String(floating));
  if (documentPDF) render(requestedPage);
});

reader.addEventListener('chapter-pdf-page', event => {
  requestedPage = event.detail;
  if (documentPDF) render(requestedPage);
});
previous.addEventListener('click', () => render(requestedPage - 1));
next.addEventListener('click', () => render(requestedPage + 1));
selector.addEventListener('change', () => render(Number(selector.value)));
zoomOut.addEventListener('click', () => {zoom = Math.max(1, zoom - .25); render(requestedPage);});
zoomIn.addEventListener('click', () => {zoom = Math.min(2.5, zoom + .25); render(requestedPage);});

try {
  documentPDF = await pdfjs.getDocument({url: reader.dataset.pdfUrl,
    cMapUrl: new URL('cmaps/', vendor).href, cMapPacked: true,
    standardFontDataUrl: new URL('standard_fonts/', vendor).href,
    wasmUrl: new URL('wasm/', vendor).href, isEvalSupported: false}).promise;
  for (let number = 1; number <= documentPDF.numPages; number++) {
    const option = document.createElement('option'); option.value = number;
    option.textContent = `Page ${number} of ${documentPDF.numPages}`; selector.append(option);
  }
  selector.disabled = false;
  await render(requestedPage);
  let width = surface.clientWidth, resizeTimer;
  new ResizeObserver(() => {
    if (surface.clientWidth === width) return;
    width = surface.clientWidth;
    clearTimeout(resizeTimer); resizeTimer = setTimeout(() => render(requestedPage), 150);
  }).observe(surface);
} catch (error) {
  console.error('Unable to load handwritten PDF:', error);
  status.textContent = 'The reader could not load. Use Open PDF to read the original.';
}

new MutationObserver(() => {
  if (!floatingChosen && !immersive) {
    floating = document.documentElement.dataset.theme === 'wuxia';
    floatingToggle.setAttribute('aria-pressed', String(floating));
  }
  if (documentPDF) render(requestedPage);
}).observe(document.documentElement, {attributes: true, attributeFilter: ['data-theme']});
