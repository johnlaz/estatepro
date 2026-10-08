// EstatePro service worker
// Keep VERSION in sync with APP_VERSION in index.html (the visible version stamp).
const VERSION = '4.0.0';
const CACHE = 'estatepro-app-v' + VERSION;
const SCOPE = self.registration.scope;
const PRECACHE = ['./', './index.html', './manifest.json', './icon-192.png', './icon-512.png']
  .map(p => new URL(p, SCOPE).href);

self.addEventListener('install', event => {
  // No skipWaiting here: the page shows "Reload" and asks us to activate (see message handler).
  event.waitUntil(caches.open(CACHE).then(c => c.addAll(PRECACHE)));
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k.startsWith('estatepro-app-') && k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('message', event => {
  if (event.data && event.data.type === 'SKIP_WAITING') self.skipWaiting();
});

self.addEventListener('fetch', event => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  // Never touch AI, map or any cross-origin traffic.
  if (url.origin !== location.origin || !url.href.startsWith(SCOPE)) return;

  const isPage = req.mode === 'navigate' || (req.headers.get('accept') || '').includes('text/html');
  if (isPage) {
    // Network-first so a new deploy shows up right away; cached copy when offline.
    event.respondWith(
      fetch(req).then(res => {
        if (res && res.ok) { const copy = res.clone(); caches.open(CACHE).then(c => c.put(new URL('./index.html', SCOPE).href, copy)); }
        return res;
      }).catch(() => caches.match(new URL('./index.html', SCOPE).href))
    );
    return;
  }
  // Cache-first for icons, manifest and screenshots.
  event.respondWith(
    caches.match(req).then(hit => hit || fetch(req).then(res => {
      if (res && res.ok) { const copy = res.clone(); caches.open(CACHE).then(c => c.put(req, copy)); }
      return res;
    }))
  );
});
