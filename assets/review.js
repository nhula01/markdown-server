import {dayKey, addDays, dailySet} from './review-schedule.mjs';
const root = document.querySelector('#daily-review');
const find = selector => document.querySelector(selector);
const base = new URL('../', import.meta.url);
const storageKey = 'physics-shared-review-v1:' + base.pathname;
const demo = new URL(location.href).searchParams.get('demo') === '1';
let states = {}, persistent = true, cards = [], session = [], position = 0, completed = 0, retry = new Set(), sessionDay = dayKey(), active = false;
try {states = demo ? {} : JSON.parse(localStorage.getItem(storageKey) || '{}'); if (!states || typeof states !== 'object' || Array.isArray(states)) states = {};}
catch {states = {}; persistent = false;}
if (states.day !== dayKey() || !Array.isArray(states.completed)) states = {day:dayKey(),completed:[]};
let pdfjs, pdf, loadingTask, pageNumber = 1, renderTask, revision = 0;
const card = () => session[position];
const status = find('[data-review-status]');
const absolute = path => new URL(path, location.origin).href;
function save() {
  if (demo) return;
  try {localStorage.setItem(storageKey, JSON.stringify(states));}
  catch {persistent = false; status.textContent = 'Browser storage is unavailable. You can review, but completion checkmarks will last only this visit.';}
}
function dashboard() {
  const today = active ? sessionDay : dayKey(), selected = dailySet(cards,today);
  find('[data-review-due]').textContent = selected.length;
  find('[data-review-today]').textContent = states.day === today ? selected.filter(c => states.completed.includes(c.id)).length : 0;
  find('[data-review-next]').textContent = 'Tomorrow';
  find('[data-review-date]').textContent = new Date(today+'T12:00:00Z').toLocaleDateString(undefined,{timeZone:'UTC',month:'long',day:'numeric',year:'numeric'});
  const list = find('[data-review-selection]'); list.replaceChildren();
  for (const [index,note] of selected.entries()) {
    const item = document.createElement('li'), name = document.createElement('strong'), label = document.createElement('span');
    name.textContent = note.title; label.textContent = `${index===0?'Today’s focus':'Return to an idea'} · ${note.topic}`;
    item.append(name,label); list.append(item);
  }
  const upcoming = find('[data-review-upcoming]'); upcoming.replaceChildren();
  for(let offset=1;offset<=7;offset++) {
    const day = addDays(today,offset), item = document.createElement('li');
    const date = document.createElement('strong'); date.textContent = new Date(day+'T12:00:00Z').toLocaleDateString(undefined,{timeZone:'UTC',month:'short',day:'numeric'}); item.append(date);
    for(const note of dailySet(cards,day)) {const link=document.createElement('a');link.textContent=note.title;link.href=absolute(note.url);item.append(link);}
    upcoming.append(item);
  }
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
    active = false;
    find('[data-review-finished]').textContent = completed ? `${completed} recall attempts completed. ${demo ? 'This sample did not save checkmarks.' : persistent ? 'Today’s checkmarks are saved on this device.' : 'Checkmarks last only this visit.'} Tomorrow’s shared selection follows the same calendar for everyone.` : 'No handwritten notebooks are available yet.';
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
  sessionDay = dayKey(); session = dailySet(cards,sessionDay); position = completed = 0; retry = new Set(); active = true;
  if(states.day !== sessionDay) states = {day:sessionDay,completed:[]};
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
  find('[data-interval="again"]').textContent = retry.has(card().id) ? 'Finish this attempt' : 'Try again at the end';
  status.textContent = 'Compare your recall with the source. Assess your recall, not how familiar the page looks.';
  for (const button of root.querySelectorAll('[data-review-grade]')) button.disabled = true;
  try {
    if (!pdfjs) {pdfjs = await import('./vendor/pdfjs-6.3.289/build/pdf.min.mjs?build=legacy'); pdfjs.GlobalWorkerOptions.workerSrc = new URL('./vendor/pdfjs-6.3.289/build/pdf.worker.min.mjs?build=legacy',import.meta.url).href;}
    const vendor = new URL('./vendor/pdfjs-6.3.289/',import.meta.url);
    loadingTask = pdfjs.getDocument({url:absolute(card().pdf),cMapUrl:new URL('cmaps/',vendor).href,cMapPacked:true,standardFontDataUrl:new URL('standard_fonts/',vendor).href,wasmUrl:new URL('wasm/',vendor).href,isEvalSupported:false});
    pdf = await loadingTask.promise;
    await renderPage(1);
  } catch {find('[data-review-page]').textContent = 'Use Open original PDF to check the handwriting.';}
  for (const button of root.querySelectorAll('[data-review-grade]')) button.disabled = false;
  find('[data-review-reveal]').hidden = true;
});
for (const button of root.querySelectorAll('[data-review-grade]')) button.addEventListener('click', async()=>{
  for (const control of root.querySelectorAll('[data-review-grade]')) control.disabled = true;
  const current = card(), rating = button.dataset.reviewGrade;
  if (!states.completed.includes(current.id)) states.completed.push(current.id); save();
  if (rating === 'again' && !retry.has(current.id)) {session.push(current); retry.add(current.id);}
  position++; completed++; dashboard(); await showCard();
});
find('[data-review-prev]').addEventListener('click',()=>{if(pdf) renderPage(pageNumber-1);});
find('[data-review-forward]').addEventListener('click',()=>{if(pdf) renderPage(pageNumber+1);});
try {
  const response = await fetch(new URL('review-index.json',base)); if (!response.ok) throw Error(); cards = await response.json();
  dashboard(); find('[data-review-start]').disabled = !cards.length;
  if (demo) {find('[data-review-start]').textContent = 'Start sample review →'; find('.review-demo-link').hidden = true;}
  status.textContent = demo ? 'Sample session · today’s shared notebooks · no checkmarks are saved.' : persistent ? 'Everyone follows the same daily calendar. Your completion checkmarks stay on this device.' : 'Everyone follows the same daily calendar. This browser cannot save completion checkmarks.';
  setInterval(()=>{if(!active) dashboard();},60_000);
} catch {status.textContent = 'The review collection could not load. Browse Notes or reload to retry.';}
