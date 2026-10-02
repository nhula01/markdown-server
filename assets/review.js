import {dayKey, interval, grade, queue} from './review-schedule.mjs';
import {accountProgress} from './review-account.mjs';
const root = document.querySelector('#daily-review');
const find = selector => document.querySelector(selector);
const base = new URL('../', import.meta.url);
const storageKey = 'physics-notebook-review-v1:' + base.pathname;
const demo = new URL(location.href).searchParams.get('demo') === '1';
let states = {}, persistent = true, cards = [], session = [], position = 0, completed = 0, retry = new Set();
try {states = demo ? {} : JSON.parse(localStorage.getItem(storageKey) || '{}'); if (!states || typeof states !== 'object' || Array.isArray(states)) states = {};}
catch {states = {}; persistent = false;}
// Ignore damaged records; never let a browser-storage problem prevent reviewing.
for (const [id,state] of Object.entries(states)) if (!state || !/^\d{4}-\d{2}-\d{2}$/.test(state.due) || !Number.isFinite(state.interval)) delete states[id];
let account, accountId = null, accountBusy = false;
let pdfjs, pdf, loadingTask, pageNumber = 1, renderTask, revision = 0;
const card = () => session[position];
const status = find('[data-review-status]');
const absolute = path => new URL(path, location.origin).href;
function save() {
  if (demo) return;
  try {localStorage.setItem(storageKey, JSON.stringify(states));}
  catch {persistent = false; status.textContent = 'Browser storage is unavailable. You can review, but your schedule will last only this visit.';}
}
function dashboard() {
  const today = dayKey();
  find('[data-review-due]').textContent = cards.filter(c => states[c.id]?.due <= today && states[c.id]?.last !== today).length;
  find('[data-review-today]').textContent = cards.filter(c => states[c.id]?.last === today).length;
  const next = cards.map(c => states[c.id]?.due).filter(Boolean).sort()[0];
  find('[data-review-next]').textContent = next ? (next <= today ? 'Today' : new Date(next+'T12:00:00').toLocaleDateString(undefined,{month:'short',day:'numeric'})) : 'Start today';
}
async function releasePDF() {
  revision++;
  if (renderTask) {renderTask.cancel(); await renderTask.promise.catch(()=>{}); renderTask = null;}
  if (loadingTask) {await loadingTask.destroy(); loadingTask = null;}
  pdf = null;
  const canvas = find('.review-pdf-surface canvas'); canvas.width = canvas.height = 0;
}
async function showCard() {
  await releasePDF();
  if (position >= session.length) {
    find('.review-card').hidden = true; find('.review-finished').hidden = false;
    find('[data-review-finished]').textContent = completed ? `${completed} recall attempts completed. ${demo ? 'This sample did not save a schedule' : accountId ? 'Your schedule is saved on this device; the account status below shows whether it has synced' : `Your next dates are saved${persistent ? ' in this browser' : ' for this visit'}`}.` : 'No notebooks are due in this collection. Your next review date is shown above.';
    status.textContent = ''; dashboard(); return;
  }
  find('.review-card').hidden = false; find('.review-check').hidden = true;
  find('[data-review-reveal]').hidden = false; find('[data-review-reveal]').disabled = false;
  find('[data-review-notebook]').textContent = card().title;
  find('#review-title').textContent = card().question;
  find('[data-review-count]').textContent = `${position+1} / ${session.length} · Recall`;
  find('[data-review-category]').textContent = card().topic;
  find('#review-response').value = '';
  status.textContent = retry.has(card().id) ? 'Try this idea again, without looking.' : 'Take a minute to recall. The source stays hidden until you are ready.';
  find('#review-title').setAttribute('tabindex','-1'); find('#review-title').focus();
}
async function renderPage(number) {
  const ticket = ++revision;
  pageNumber = Math.max(1,Math.min(number,pdf.numPages));
  find('[data-review-page]').textContent = 'Loading handwritten page…';
  try {
    if (renderTask) {renderTask.cancel(); await renderTask.promise.catch(()=>{});}
    const page = await pdf.getPage(pageNumber); if (ticket !== revision) return;
    const canvas = find('.review-pdf-surface canvas');
    const width = find('.review-pdf-surface').clientWidth-24;
    const viewport = page.getViewport({scale:Math.max(1,width)/page.getViewport({scale:1}).width});
    const density = Math.min(devicePixelRatio || 1,2,Math.sqrt(8_000_000/(viewport.width*viewport.height)),4096/Math.max(viewport.width,viewport.height));
    canvas.width = Math.ceil(viewport.width*density); canvas.height = Math.ceil(viewport.height*density);
    canvas.style.width = `${viewport.width}px`; canvas.style.height = `${viewport.height}px`;
    canvas.setAttribute('aria-label',`${card().title}, handwritten page ${pageNumber}`);
    renderTask = page.render({canvasContext:canvas.getContext('2d'),viewport,transform:[density,0,0,density,0,0]});
    await renderTask.promise; if (ticket !== revision) return;
    find('[data-review-page]').textContent = `Page ${pageNumber} of ${pdf.numPages}`;
    find('[data-review-prev]').disabled = pageNumber === 1;
    find('[data-review-forward]').disabled = pageNumber === pdf.numPages;
  } catch(error) {
    if (error.name !== 'RenderingCancelledException') find('[data-review-page]').textContent = 'Use Open original PDF to check the handwriting.';
  }
}
find('[data-review-start]').addEventListener('click',async()=>{
  session = queue(cards,states,dayKey(),find('#review-topic').value); position = completed = 0; retry = new Set();
  find('.review-setup').hidden = true; find('.review-finished').hidden = true; await showCard();
});
find('[data-review-reveal]').addEventListener('click',async()=>{
  find('[data-review-reveal]').disabled = true;
  find('.review-check').hidden = false;
  find('[data-review-open]').href = absolute(card().url);
  find('[data-review-pdf]').href = absolute(card().pdf);
  const guide = find('[data-review-guide]'); guide.textContent = card().guide;
  find('.review-guide').hidden = !card().guide.trim();
  find('.review-guide').open = false;
  if (window.renderMathInElement) window.renderMathInElement(guide,{delimiters:[{left:'$$',right:'$$',display:true},{left:'$',right:'$',display:false},{left:'\\(',right:'\\)',display:false},{left:'\\[',right:'\\]',display:true}],throwOnError:false,trust:false});
  for (const choice of ['again','shaky','good','easy']) {
    const days = interval(states[card().id],choice);
    find(`[data-interval="${choice}"]`).textContent = `${choice === 'again' && !retry.has(card().id) && session.length < 5 ? 'Retry, then ' : ''}${days === 1 ? 'tomorrow' : `in ${days} days`}`;
  }
  status.textContent = 'Compare your recall with the source. Assess your recall, not how familiar the page looks.';
  for (const button of root.querySelectorAll('[data-review-grade]')) button.disabled = true;
  try {
    if (!pdfjs) {pdfjs = await import('./vendor/pdfjs-6.3.289/build/pdf.min.mjs?build=legacy'); pdfjs.GlobalWorkerOptions.workerSrc = new URL('./vendor/pdfjs-6.3.289/build/pdf.worker.min.mjs?build=legacy',import.meta.url).href;}
    const vendor = new URL('./vendor/pdfjs-6.3.289/',import.meta.url);
    loadingTask = pdfjs.getDocument({url:absolute(card().pdf),cMapUrl:new URL('cmaps/',vendor).href,cMapPacked:true,standardFontDataUrl:new URL('standard_fonts/',vendor).href,wasmUrl:new URL('wasm/',vendor).href,isEvalSupported:false});
    pdf = await loadingTask.promise;
    await renderPage(1);
  } catch {find('[data-review-page]').textContent = 'Use Open original PDF to check the handwriting.';}
  for (const button of root.querySelectorAll('[data-review-grade]')) button.disabled = accountBusy;
  find('[data-review-reveal]').hidden = true;
});
for (const button of root.querySelectorAll('[data-review-grade]')) button.addEventListener('click', async()=>{
  for (const control of root.querySelectorAll('[data-review-grade]')) control.disabled = true;
  const current = card(), rating = button.dataset.reviewGrade;
  if (account?.signedIn()) account.record(current.id,rating,dayKey());
  else {states[current.id] = grade(states[current.id],rating,dayKey()); save();}
  if (rating === 'again' && !retry.has(current.id) && session.length < 5) {session.push(current); retry.add(current.id);}
  position++; completed++; dashboard(); await showCard();
});
find('[data-review-prev]').addEventListener('click',()=>{if(pdf) renderPage(pageNumber-1);});
find('[data-review-forward]').addEventListener('click',()=>{if(pdf) renderPage(pageNumber+1);});
try {
  const response = await fetch(new URL('review-index.json',base)); if (!response.ok) throw Error(); cards = await response.json();
  for (const topic of [...new Set(cards.map(c=>c.topic))]) {const option=document.createElement('option');option.value=option.textContent=topic;find('#review-topic').append(option);}
  account = await accountProgress({base,demo,
    changed(next, uid) {
      const previous = accountId; accountId = uid || null;
      if (next) states = next;
      else {try {states = JSON.parse(localStorage.getItem(storageKey) || '{}');} catch {states={};}}
      dashboard();
      if (previous !== accountId) {
        releasePDF(); session = []; position = completed = 0;
        find('.review-card').hidden = find('.review-finished').hidden = true;
        find('.review-setup').hidden = false;
        status.textContent = accountId ? 'Account schedule · up to five notebooks. Your account status shows whether progress has synced.' : 'Guest schedule · your progress stays on this device.';
      }
    },
    busy(value) {
      accountBusy = value;
      find('[data-review-start]').disabled = value;
      for (const control of document.querySelectorAll('.review-account button')) control.disabled = value;
      for (const control of root.querySelectorAll('[data-review-grade]')) control.disabled = value || !pdf;
    }
  });
  dashboard(); find('[data-review-start]').disabled = false;
  if (demo) {find('[data-review-start]').textContent = 'Start sample review →'; find('.review-demo-link').hidden = true;}
  status.textContent = demo ? 'Sample session · original notebooks · no schedule is saved.' : accountId ? 'Account schedule · up to five notebooks. Your account status shows whether progress has synced.' : persistent ? 'Up to five notebooks · at most two new ones · your progress stays on this device.' : 'Your browser cannot save progress. You can still review during this visit.';
} catch {status.textContent = 'The review collection could not load. Browse Notes or reload to retry.';}
