import test from 'node:test';
import assert from 'node:assert/strict';
import {replay,validateConfig} from '../assets/review-events.mjs';
const event=(id,day,rating='good',notebook='A.pdf')=>({id,review_day:day,rating,notebook_id:notebook,recorded_at:day+'T12:00:00Z'});
test('retries are idempotent and independent device reviews are preserved',()=>{
 const a=event('a','2026-10-02'), b=event('b','2026-10-05');
 assert.deepEqual(replay([b,a,a]),replay([a,b]));
 assert.equal(replay([b,a,a])['A.pdf'].reviews,2);
 assert.equal(replay([b,a])['A.pdf'].due,'2026-10-12');
});
test('offline reviews replay by recall day rather than late upload day',()=>{
 const a=event('a','2026-10-02','again'),b=event('b','2026-10-03');
 a.recorded_at='2026-10-04T12:00:00Z';
 assert.equal(replay([b,a])['A.pdf'].last,'2026-10-03');
 assert.equal(replay([b,a])['A.pdf'].interval,3);
});
test('separate account event collections never share schedules',()=>{
 assert.equal(replay([event('a','2026-10-02')])['A.pdf'].reviews,1);
 assert.deepEqual(replay([]),{});
});
test('configuration accepts public keys only, and rejects unsafe endpoints',()=>{
 assert.equal(validateConfig({url:'',publishableKey:''}),null);
 assert.equal(validateConfig({url:'https://example.supabase.co',publishableKey:'sb_publishable_abc'}).url,'https://example.supabase.co');
 for(const url of ['http://example.supabase.co','https://evil.com','https://example.supabase.co@evil.com','https://example.supabase.co/path']) assert.throws(()=>validateConfig({url,publishableKey:'sb_publishable_abc'}));
 for(const publishableKey of ['sb_secret_abc','eyJ.service-role.jwt','']) assert.throws(()=>validateConfig({url:'https://example.supabase.co',publishableKey}));
});

import {syncEvents} from '../assets/review-cloud.mjs';
function fakeServer() {
 const records=new Map(); let failRead=false; const insertions=[];
 const client={from(name){assert.equal(name,'review_events'); let uid;
  const chain={select(){return chain;},eq(column,value){assert.equal(column,'user_id');uid=value;return chain;},order(){return chain;},async range(start,end){if(failRead) return {error:{code:'network'}};return {data:[...records.values()].filter(x=>x.user_id===uid).slice(start,end+1),error:null};},async insert(record){insertions.push(record);if(records.has(record.id))return {error:{code:'23505'}};records.set(record.id,{...record,recorded_at:'2026-10-02T14:00:00Z'});return {error:null};}};return chain;}};
 return {client,records,insertions,failRead(value){failRead=value;}};
}
test('interrupted read retries an event without losing it or adding a duplicate',async()=>{
 const server=fakeServer(), pending=[event('one','2026-10-02')];
 server.failRead(true);await assert.rejects(syncEvents(server.client,'userA',pending));
 assert.equal(pending.length,1);assert.equal(server.records.size,1);
 server.failRead(false);const received=await syncEvents(server.client,'userA',pending);
 assert.equal(received.length,1);assert.equal(server.records.size,1);
 assert.equal(server.insertions[0].user_id,'userA');
 assert.equal('recorded_at' in server.insertions[0],false);
});
test('requests filter to the active user and fetch history beyond a single page',async()=>{
 const server=fakeServer();
 for(let i=0;i<1002;i++)server.records.set(String(i),{...event(String(i),'2026-10-02'),user_id:i===1001?'other':'userA'});
 const received=await syncEvents(server.client,'userA',[]);
 assert.equal(received.length,1001);assert.ok(received.every(row=>row.user_id==='userA'));
});
