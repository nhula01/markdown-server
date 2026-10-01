import * as pdfjs from './vendor/pdfjs-6.3.289/build/pdf.min.mjs';

const reader = document.querySelector('.pdf-reader');
const vendor = new URL('./vendor/pdfjs-6.3.289/', import.meta.url);
pdfjs.GlobalWorkerOptions.workerSrc = new URL('build/pdf.worker.min.mjs', vendor).href;
const canvas = reader.querySelector('canvas');
const surface = reader.querySelector('.pdf-surface');
const status = reader.querySelector('[data-pdf-status]');
const selector = reader.querySelector('[data-pdf-select]');
const previous = reader.querySelector('[data-pdf-previous]');
const next = reader.querySelector('[data-pdf-next]');
const zoomOut = reader.querySelector('[data-pdf-zoom-out]');
const zoomIn = reader.querySelector('[data-pdf-zoom-in]');
let documentPDF, requestedPage = Number(reader.dataset.page || 1), zoom = 1, revision = 0, renderTask;

async function render(number) {
  requestedPage = Math.max(1, Math.min(number, documentPDF.numPages));
  const ticket = ++revision;
  status.textContent = `Loading page ${requestedPage}…`;
  try {
    if (renderTask) {renderTask.cancel(); await renderTask.promise.catch(() => {});}
    const page = await documentPDF.getPage(requestedPage);
    if (ticket !== revision) return;
    const fit = (surface.clientWidth - 2) / page.getViewport({scale: 1}).width;
    const viewport = page.getViewport({scale: fit * zoom});
    const density = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.ceil(viewport.width * density);
    canvas.height = Math.ceil(viewport.height * density);
    canvas.style.width = `${viewport.width}px`;
    canvas.style.height = `${viewport.height}px`;
    canvas.setAttribute('aria-label', `${reader.dataset.title}, handwritten page ${requestedPage} of ${documentPDF.numPages}`);
    renderTask = page.render({canvasContext: canvas.getContext('2d'), viewport,
      transform: [density, 0, 0, density, 0, 0]});
    await renderTask.promise;
    if (ticket !== revision) return;
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
