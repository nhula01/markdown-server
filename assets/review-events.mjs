import {grade} from './review-schedule.mjs';

// The server stores immutable recall events, so two devices cannot overwrite
// one another's progress. Duplicate uploads have the same UUID.
export function replay(events) {
  const states = {}, seen = new Set();
  const valid = events.filter(event => event && typeof event.id === 'string' && typeof event.notebook_id === 'string'
    && event.notebook_id.length > 0 && event.notebook_id.length <= 512
    && ['again','shaky','good','easy'].includes(event.rating)
    && typeof event.review_day === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(event.review_day)
    && typeof event.recorded_at === 'string');
  for (const event of valid.sort((a,b) => a.review_day.localeCompare(b.review_day) || a.recorded_at.localeCompare(b.recorded_at) || a.id.localeCompare(b.id))) {
    if (seen.has(event.id)) continue;
    seen.add(event.id);
    Object.defineProperty(states,event.notebook_id,{value:grade(Object.hasOwn(states,event.notebook_id)?states[event.notebook_id]:null,event.rating,event.review_day),enumerable:true,configurable:true});
  }
  return states;
}

export function validateConfig(config) {
  if (!config.url && !config.publishableKey) return null;
  const url = new URL(config.url);
  if (url.protocol !== 'https:' || !/^[a-z0-9-]+\.supabase\.co$/.test(url.hostname) || url.pathname !== '/' || url.search || url.hash || url.username || url.password) throw Error('Use the HTTPS Supabase project URL.');
  // Only the modern public key is supported. Never package administrative keys.
  if (!/^sb_publishable_[A-Za-z0-9_-]+$/.test(config.publishableKey)) throw Error('Use a public Supabase publishable key, never a secret key.');
  return {url:url.origin, key:config.publishableKey};
}
