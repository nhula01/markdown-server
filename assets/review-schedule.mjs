// A UTC calendar gives everyone the same selection regardless of location.
export function dayKey(date = new Date()) {return date.toISOString().slice(0,10);}
export function addDays(key, days) {
  const date = new Date(key+'T12:00:00Z'); date.setUTCDate(date.getUTCDate()+days);
  return dayKey(date);
}
export function dailySet(cards, day = dayKey()) {
  const groups = new Map(), unique = new Map(cards.map(card=>[card.id,card]));
  const compare = (a,b) => a < b ? -1 : a > b ? 1 : 0;
  for(const card of [...unique.values()].sort((a,b)=>compare(a.id,b.id))) {
    const topic = card.topic || ''; if(!groups.has(topic)) groups.set(topic,[]); groups.get(topic).push(card);
  }
  const buckets = [...groups].sort((a,b)=>compare(a[0],b[0])).map(([,notes])=>notes);
  const rotation=[];
  while(buckets.some(bucket=>bucket.length)) for(const bucket of buckets) if(bucket.length) rotation.push(bucket.shift());
  if(!rotation.length) return [];
  const elapsed = Math.floor((Date.parse(day+'T00:00:00Z')-Date.UTC(2026,9,2))/86_400_000);
  if(!Number.isFinite(elapsed)) throw Error('Invalid review date');
  const index = number => ((number % rotation.length)+rotation.length)%rotation.length;
  const focus = rotation[index(elapsed)];
  if(rotation.length===1) return [focus];
  const revisit = rotation[index(elapsed-3)] || focus;
  return [focus,revisit.id===focus.id?rotation[index(elapsed-1)]:revisit];
}
