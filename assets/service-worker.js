const VERSION = '__BUILD_VERSION__';
const BASE = new URL('./', self.location.href);
const PREFIX = 'physics-review:' + BASE.pathname + ':';
const CACHE = PREFIX + VERSION;
const MARKER = new URL('__offline_ready__', BASE).href;
const url = path => new URL(path, BASE).href;
self.addEventListener('install', event => {
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE);
    await cache.addAll(['notes/review/', 'style.css', 'assets/pwa.js', 'assets/review.js', 'assets/review-schedule.mjs', 'review-index.json'].map(url));
    await self.skipWaiting();
  })());
});
self.addEventListener('activate', event => event.waitUntil(self.clients.claim()));
let download;
async function downloadAll(port) {
  const response = await fetch(url('offline-index.json'), {cache:'no-store'});
  if (!response.ok) throw Error('The download list is unavailable.');
  const {files} = await response.json();
  const cache = await caches.open(CACHE);
  // Remove the marker first: an interrupted refresh must never report ready.
  await cache.delete(MARKER);
  let done = 0;
  for (const file of files) {
    const target = new URL(file, BASE);
    if (target.origin !== BASE.origin || !target.pathname.startsWith(BASE.pathname)) throw Error('Invalid offline file.');
    const result = await fetch(target, {cache:'reload'});
    if (!result.ok) throw Error('A notebook could not download.');
    await cache.put(target, result);
    port.postMessage({type:'progress', done:++done, total:files.length});
  }
  await cache.put(MARKER, new Response(VERSION));
  for (const key of await caches.keys()) if (key.startsWith(PREFIX) && key !== CACHE) await caches.delete(key);
}
self.addEventListener('message', event => {
  const port = event.ports[0]; if (!port) return;
  event.waitUntil((async () => {
    try {
      if (event.data.type === 'status') {
        port.postMessage({ready:!!(await (await caches.open(CACHE)).match(MARKER))});
      } else if (event.data.type === 'download') {
        if (download) throw Error('A download is already running. Wait for it to finish.');
        download = downloadAll(port);
        try {await download;} finally {download = null;}
        port.postMessage({type:'done'});
      }
    } catch (error) {port.postMessage({error:error.message});}
  })());
});
async function cachedResponse(request) {
  const keys = [CACHE, ...(await caches.keys()).filter(key => key.startsWith(PREFIX) && key !== CACHE).reverse()];
  for (const key of keys) {
    const hit = await (await caches.open(key)).match(request, {ignoreSearch:true});
    if (!hit) continue;
    const range = request.headers.get('range');
    if (!range) return hit;
    const bytes = await hit.arrayBuffer();
    const match = /^bytes=(\d*)-(\d*)$/.exec(range);
    if (!match || (!match[1] && !match[2])) return new Response(null, {status:416, headers:{'Content-Range':`bytes */${bytes.byteLength}`}});
    const start = match[1] ? Number(match[1]) : Math.max(0, bytes.byteLength - Number(match[2]));
    const end = match[1] && match[2] ? Math.min(Number(match[2]), bytes.byteLength - 1) : bytes.byteLength - 1;
    if (start > end || start >= bytes.byteLength) return new Response(null, {status:416, headers:{'Content-Range':`bytes */${bytes.byteLength}`}});
    return new Response(bytes.slice(start, end + 1), {status:206, headers:{'Content-Type':hit.headers.get('Content-Type') || 'application/octet-stream', 'Content-Range':`bytes ${start}-${end}/${bytes.byteLength}`, 'Content-Length':String(end-start+1), 'Accept-Ranges':'bytes'}});
  }
}
self.addEventListener('fetch', event => {
  const target = new URL(event.request.url);
  if (event.request.method !== 'GET' || target.origin !== BASE.origin || !target.pathname.startsWith(BASE.pathname)) return;
  event.respondWith((async () => {
    try {const response = await fetch(event.request); if (response.ok || response.status === 206) return response;} catch {}
    const cached = await cachedResponse(event.request);
    if (cached) return cached;
    return new Response('This page is not downloaded. Reconnect and use Download for offline review.', {status:503, headers:{'Content-Type':'text/plain; charset=utf-8'}});
  })());
});
