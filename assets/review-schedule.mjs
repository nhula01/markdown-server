// Calendar days rather than 24-hour periods: works across local daylight changes.
export function dayKey(date = new Date()) {
  return `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')}`;
}
export function addDays(key, days) {
  const [year, month, day] = key.split('-').map(Number);
  return dayKey(new Date(year, month-1, day+days, 12));
}
export function interval(previous, rating) {
  if (rating === 'again' || rating === 'shaky') return 1;
  const old = previous?.interval || 0;
  if (rating === 'easy') return Math.min(90, Math.max(7, old * 2));
  return [3, 7, 14, 30, 60, 90].find(days => days > old) || 90;
}
export function grade(previous, rating, today) {
  const days = interval(previous, rating);
  return {interval: days, due: addDays(today, days), last: today,
    reviews: (previous?.reviews || 0)+1, introduced: previous?.introduced || today};
}
export function queue(cards, states, today, topic = '') {
  const available = cards.filter(card => !topic || card.topic === topic);
  const due = available.filter(card => states[card.id] && states[card.id].due <= today && states[card.id].last !== today)
    .sort((a,b) => states[a.id].due.localeCompare(states[b.id].due));
  const newToday = Object.values(states).filter(state => state.introduced === today).length;
  const fresh = available.filter(card => !states[card.id]);
  const ordered = [];
  // Interleave within due cards first, then within new cards.
  for (const [pending, limit] of [[due,5],[fresh,Math.max(0,2-newToday)]]) {
    let remaining = limit;
    while (remaining > 0 && pending.length && ordered.length < 5) {
    const next = pending.findIndex(card => card.topic !== ordered.at(-1)?.topic);
    ordered.push(pending.splice(next < 0 ? 0 : next, 1)[0]); remaining--;
    }
  }
  return ordered;
}
