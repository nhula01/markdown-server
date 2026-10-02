import test from 'node:test';
import assert from 'node:assert/strict';
import {addDays, grade, interval, queue} from '../assets/review-schedule.mjs';
const today = '2026-10-02';
const cards = [{id:'a',topic:'Fields'},{id:'b',topic:'Fields'},{id:'c',topic:'Matter'},{id:'d',topic:'Quantum'}];
test('calendar scheduling crosses month, year, and leap day boundaries',()=>{
 assert.equal(addDays('2026-12-31',1),'2027-01-01');
 assert.equal(addDays('2028-02-28',1),'2028-02-29');
 assert.equal(addDays('2026-03-07',2),'2026-03-09');
});
test('successful recall expands spacing while failed recall comes back tomorrow',()=>{
 let state;
 for (const days of [3,7,14,30,60,90,90]) {state=grade(state,'good',today);assert.equal(state.interval,days);}
 assert.equal(grade(state,'again',today).due,'2026-10-03');
 assert.equal(grade(state,'shaky',today).interval,1);
 assert.equal(interval(undefined,'easy'),7);
 assert.equal(interval({interval:60},'easy'),90);
});
test('new notebooks are capped across sessions on the same day',()=>{
 assert.deepEqual(queue(cards,{},today).map(c=>c.id),['a','c']);
 const states={a:grade(undefined,'good',today),c:grade(undefined,'good',today)};
 assert.deepEqual(queue(cards,states,today),[]);
 assert.deepEqual(queue(cards,states,'2026-10-03').map(c=>c.id),['b','d']);
});
test('due notebooks precede new ones and mix topics where possible',()=>{
 const states={a:{due:'2026-10-01',last:'2026-09-25'},b:{due:'2026-10-01',last:'2026-09-25'},c:{due:today,last:'2026-09-25'}};
 assert.deepEqual(queue(cards,states,today).map(c=>c.id),['a','c','b','d']);
 assert.deepEqual(queue(cards,states,today,'Matter').map(c=>c.id),['c']);
});
test('future and already-reviewed cards are excluded and sessions stay bounded',()=>{
 const many=Array.from({length:20},(_,i)=>({id:String(i),topic:'Fields'}));
 const states=Object.fromEntries(many.map(c=>[c.id,{due:today,last:'2026-09-25'}]));
 states['0'].last=today;states['1'].due='2026-10-04';
 const result=queue(many,states,today);
 assert.equal(result.length,5);assert.ok(!result.some(c=>['0','1'].includes(c.id)));
});
