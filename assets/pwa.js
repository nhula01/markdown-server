(() => {
  const base = new URL('../', document.currentScript.src);
  const install = document.querySelector('[data-app-install]');
  const download = document.querySelector('[data-offline-download]');
  const status = document.querySelector('[data-offline-status]');
  let prompt;
  window.addEventListener('beforeinstallprompt', event => {
    event.preventDefault(); prompt = event;
    if (install) install.hidden = false;
  });
  install?.addEventListener('click', async () => {
    if (!prompt) return;
    await prompt.prompt(); await prompt.userChoice; prompt = null; install.hidden = true;
  });
  window.addEventListener('appinstalled', () => {if (install) install.hidden = true;});
  if (!('serviceWorker' in navigator) || !window.isSecureContext) {
    if (status) status.textContent = 'Offline review needs a browser with service worker support and an HTTPS connection. Online review is available below.';
    return;
  }
  async function message(worker, type, progress) {
    return new Promise((resolve, reject) => {
      const channel = new MessageChannel();
      let timeout;
      const reset = () => {clearTimeout(timeout); timeout = setTimeout(() => {channel.port1.close(); reject(Error('Download timed out. Stay connected and try again.'));}, 60000);};
      reset();
      channel.port1.onmessage = ({data}) => {
        reset();
        if (data.type === 'progress') {progress?.(data); return;}
        clearTimeout(timeout); channel.port1.close();
        if (data.error) reject(Error(data.error)); else resolve(data);
      };
      worker.postMessage({type}, [channel.port2]);
    });
  }
  (async () => {
    try {
      await navigator.serviceWorker.register(new URL('sw.js', base), {scope:base.pathname, updateViaCache:'none'});
      const registration = await navigator.serviceWorker.ready;
      const worker = () => registration.active;
      if (!download) return;
      const result = await message(worker(), 'status');
      status.textContent = result.ready ? 'Notebooks downloaded. Offline review is ready on this device.' : 'Download the review pages and handwritten notebooks to use without a connection.';
      download.disabled = false;
      download.textContent = result.ready ? 'Refresh offline download' : 'Download for offline review';
      download.addEventListener('click', async () => {
        download.disabled = true;
        try {
          if (navigator.storage?.persist) await navigator.storage.persist().catch(() => false);
          status.textContent = 'Preparing your offline notebook…';
          await message(worker(), 'download', data => {status.textContent = `Downloading ${data.done} of ${data.total} files… Keep this page open.`;});
          status.textContent = 'Download complete. Your review and handwritten notebooks are ready offline on this device.';
          download.textContent = 'Refresh offline download';
        } catch (error) {status.textContent = `${error.message} Reconnect and try the download again.`;}
        finally {download.disabled = false;}
      });
    } catch {if (status) status.textContent = 'Offline setup could not finish. Reconnect and reload to try again. Online review is available below.';}
  })();
})();
