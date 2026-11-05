import {test} from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFileSync} from 'node:fs';

test('offline download supports versioned URLs, PDF ranges, and interrupted refresh', async () => {
  const handlers = {}, stores = new Map(); let offline = false, fail = false;
  const origin = 'https://example.org/markdown-server/';
  const normalize = (value, ignore = false) => {const u = new URL(typeof value === 'string' ? value : value.url || value.href); if (ignore) u.search = ''; return u.href;};
  const caches = {
    async open(name) {
      if (!stores.has(name)) stores.set(name, new Map()); const store = stores.get(name);
      return {
        async addAll() {},
        async put(key, response) {store.set(normalize(key), response.clone());},
        async delete(key) {return store.delete(normalize(key));},
        async match(key, options) {const target = normalize(key, options?.ignoreSearch); for (const [url, value] of store) if (normalize(url, options?.ignoreSearch) === target) return value.clone();},
      };
    },
    async keys() {return [...stores.keys()];},
    async delete(key) {return stores.delete(key);},
  };
  const context = vm.createContext({URL, Request, Response, caches,
    fetch:async input => {
      if (offline) throw Error('offline'); const address = normalize(input);
      if (address.endsWith('offline-index.json')) return Response.json({files:[origin+'notes/review/', origin+'pdfs/note.pdf']});
      if (fail && address.endsWith('.pdf')) throw Error('interrupted');
      return new Response(address.endsWith('.pdf') ? '0123456789' : '<h1>Review</h1>');
    },
    self:{location:{href:origin+'sw.js'},addEventListener:(name, fn)=>handlers[name]=fn},
  });
  vm.runInContext(readFileSync('assets/service-worker.js', 'utf8'), context);
  async function message(type) {
    const responses = []; let pending;
    handlers.message({data:{type},ports:[{postMessage:data=>responses.push(data)}],waitUntil:value=>pending=value});
    await pending; return responses.at(-1);
  }
  async function request(path, headers) {
    let response; handlers.fetch({request:new Request(origin+path, {headers}),respondWith:value=>response=value}); return response;
  }
  assert.equal((await message('status')).ready, false);
  assert.equal((await message('download')).type, 'done');
  assert.equal((await message('status')).ready, true);
  offline = true;
  assert.equal(await (await request('notes/review/?v=new')).text(), '<h1>Review</h1>');
  const range = await request('pdfs/note.pdf?v=123', {range:'bytes=2-5'});
  assert.equal(range.status, 206); assert.equal(await range.text(), '2345');
  assert.equal(range.headers.get('content-range'), 'bytes 2-5/10');
  assert.equal((await request('pdfs/note.pdf', {range:'bytes=15-'})).status, 416);
  assert.equal((await request('missing/')).status, 503);
  offline = false; fail = true;
  assert.match((await message('download')).error, /interrupted/);
  assert.equal((await message('status')).ready, false);
  offline = true;
  assert.equal(await (await request('pdfs/note.pdf')).text(), '0123456789');
});
