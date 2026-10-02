import test from 'node:test';
import assert from 'node:assert/strict';
import {dayKey,addDays,dailySet} from '../assets/review-schedule.mjs';
const cards=[{id:'a',topic:'Fields'},{id:'b',topic:'Fields'},{id:'c',topic:'Matter'},{id:'d',topic:'Quantum'}];
test('one UTC calendar across time zones and day boundaries',()=>{
 assert.equal(dayKey(new Date('2026-10-02T18:00:00-07:00')),'2026-10-03');
 assert.equal(dayKey(new Date('2026-10-03T10:00:00+09:00')),'2026-10-03');
 assert.equal(addDays('2026-12-31',1),'2027-01-01');
 assert.equal(addDays('2028-02-28',1),'2028-02-29');
});
test('everyone gets the same set regardless of input ordering or progress',()=>{
 assert.deepEqual(dailySet(cards,'2026-10-02'),dailySet([...cards].reverse(),'2026-10-02'));
 assert.deepEqual(dailySet(cards,'2026-10-02').map(c=>c.id),['a','c']);
});
test('focus rotates across every notebook and revisits after three days',()=>{
 const focus=Array.from({length:cards.length},(_,i)=>dailySet(cards,addDays('2026-10-02',i))[0]);
 assert.equal(new Set(focus.map(c=>c.id)).size,cards.length);
 assert.equal(dailySet(cards,'2026-10-05')[1].id,dailySet(cards,'2026-10-02')[0].id);
});
test('empty and small libraries have no duplicate daily notebooks',()=>{
 assert.deepEqual(dailySet([]),[]);
 assert.deepEqual(dailySet(cards.slice(0,1)),cards.slice(0,1));
 for(const size of [2,3,4])for(let i=-4;i<8;i++) {
  const result=dailySet(cards.slice(0,size),addDays('2026-10-02',i));
  assert.equal(result.length,2);assert.notEqual(result[0].id,result[1].id);
 }
});
