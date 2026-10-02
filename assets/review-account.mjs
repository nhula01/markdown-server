import {replay, validateConfig} from './review-events.mjs';
import {syncEvents} from './review-cloud.mjs';

export async function accountProgress({base, demo, changed, busy}) {
  const find = selector => document.querySelector(selector);
  const message = find('[data-account-status]'), form = find('[data-account-form]');
  const logout = find('[data-account-logout]'), sync = find('[data-account-sync]');
  const recovery = find('[data-account-recovery]');
  let client, user = null, cached = [], pending = [], serial = Promise.resolve(), booting = true, tasks = 0, storageOK = true;
  const key = uid => `physics-review-account-v1:${base.pathname}:${uid}`;
  const redirectTo = new URL('review/',base).href;
  const notify = text => {message.textContent = text;};
  const update = () => changed(replay([...cached,...pending]),user.id);
  function remember() {
    try {localStorage.setItem(key(user.id),JSON.stringify({cached,pending}));}
    catch {storageOK = false;}
  }
  function enqueue(task) {
    tasks++; busy(true);
    const result = serial.then(task);
    serial = result.catch(()=>{}).finally(()=>{tasks--; busy(tasks > 0);});
    return result;
  }
  async function synchronize() {
    if (!user) return;
    notify('Syncing your review progress…');
    try {
      const received = await syncEvents(client,user.id,[...pending]);
      // Keep pending events until the server confirms them on a successful read.
      // Network interruption between insert and fetch never loses local progress.
      const acknowledged = new Set(received.map(event=>event.id));
      pending = pending.filter(event=>!acknowledged.has(event.id));
      cached = received; remember(); update();
      notify(pending.length ? 'Some reviews are still waiting to sync. Use Sync again.' : storageOK ? 'Signed in · progress synced across your devices.' : 'Synced. This browser cannot keep an offline copy.');
    } catch {
      update();
      notify(pending.length ? `Not synced · ${pending.length} reviews waiting on this device. Use Sync again when online.${storageOK?'':' Keep this tab open until they sync.'}` : 'Could not reach your account. Showing the last saved progress; use Sync again when online.');
    }
  }
  async function adopt(next) {
    if ((next?.id || null) === (user?.id || null)) return;
    user = next; cached = []; pending = []; storageOK = true;
    form.hidden = !!user; logout.hidden = sync.hidden = !user;
    if (!user) {recovery.hidden = true; changed(null,false); notify('Guest · progress stays on this device.'); return;}
    try {const saved = JSON.parse(localStorage.getItem(key(user.id)) || '{}'); cached = Array.isArray(saved.cached)?saved.cached:[]; pending=Array.isArray(saved.pending)?saved.pending:[];}
    catch {storageOK = false;}
    update(); await synchronize();
  }
  form.addEventListener('submit',event=>{
    event.preventDefault();
    if (!client || !form.reportValidity()) return;
    const action = event.submitter?.dataset.accountAction || 'login';
    const email = find('#account-email').value.trim(), password = find('#account-password').value;
    find('#account-password').value = '';
    enqueue(async()=>{
      if (action === 'signup') {
        const {data,error} = await client.auth.signUp({email,password,options:{emailRedirectTo:redirectTo}});
        if (error) {notify('Could not create the account. Check your details and try again later.'); return;}
        if (data.session) await adopt(data.session.user);
        else notify('Check your email for a confirmation link, then sign in. If you already have an account, use Sign in.');
      } else {
        const {data,error} = await client.auth.signInWithPassword({email,password});
        if (error) {notify('Could not sign in. Check your email, password, and email confirmation.'); return;}
        await adopt(data.user);
      }
    }).catch(()=>notify('Account service is unavailable. You can continue as a guest.'));
  });
  find('[data-account-reset]').addEventListener('click',()=>{
    if (!client || !find('#account-email').reportValidity()) return;
    enqueue(async()=>{
      const {error} = await client.auth.resetPasswordForEmail(find('#account-email').value.trim(),{redirectTo});
      notify(error ? 'Could not request a reset. Please try again later.' : 'If that email has an account, a password-reset link will arrive shortly.');
    }).catch(()=>notify('Could not request a reset. Please try again later.'));
  });
  recovery.addEventListener('submit',event=>{
    event.preventDefault();
    if (!client || !user || !recovery.reportValidity()) return;
    const password = find('#account-new-password').value; find('#account-new-password').value = '';
    enqueue(async()=>{
      const {error} = await client.auth.updateUser({password});
      if (error) {notify('Could not change your password. Please try again.'); return;}
      recovery.hidden = true; notify('Password updated. Your progress is unchanged.');
    }).catch(()=>notify('Could not change your password. Please try again.'));
  });
  logout.addEventListener('click',()=>enqueue(async()=>{
    const {error} = await client.auth.signOut({scope:'local'});
    if (error) {notify('Could not sign out. Please retry.'); return;}
    await adopt(null);
  }).catch(()=>notify('Could not sign out. Please retry.')));
  sync.addEventListener('click',()=>enqueue(synchronize));
  try {
    if (demo) {notify('Sample session · accounts are disabled here.'); return null;}
    const response = await fetch(new URL('auth-config.json',base),{cache:'no-store'});
    if (!response.ok) throw Error();
    const config = validateConfig(await response.json());
    if (!config) {notify('Guest · account sync is awaiting setup. You can review on this device now.'); return null;}
    const {createClient} = await import('./vendor/supabase/supabase.mjs');
    client = createClient(config.url,config.key,{auth:{flowType:'pkce',persistSession:true,autoRefreshToken:true,detectSessionInUrl:true,storageKey:`physics-review-auth:${base.pathname}`}});
    let recovering = false;
    client.auth.onAuthStateChange((event,session)=>{
      if (event === 'PASSWORD_RECOVERY') recovering = true;
      // Queue outside the SDK auth lock, including startup callback processing.
      if (!booting) setTimeout(()=>enqueue(async()=>{await adopt(session?.user || null); if(recovering && user) recovery.hidden=false;}),0);
    });
    const {data,error} = await client.auth.getSession();
    if (error) throw error;
    await enqueue(()=>adopt(data.session?.user || null));
    booting = false;
    find('[data-account-fields]').disabled = false;
    if (recovering && user) recovery.hidden = false;
    if (!user) notify('Guest · sign in or create an account to sync a new schedule. Your guest schedule stays separate.');
    window.addEventListener('online',()=>{if(user) enqueue(synchronize);});
    return {
      signedIn:()=>!!user,
      record(notebook_id,rating,review_day) {
        if (!user) return;
        pending.push({id:crypto.randomUUID(),notebook_id,rating,review_day,recorded_at:new Date().toISOString()});
        remember(); update();
        return enqueue(synchronize);
      }
    };
  } catch {
    booting = false; notify('Account sign-in is unavailable. You can still review as a guest.'); return null;
  }
}
