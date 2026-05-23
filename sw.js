// LazEstate Landing Page Service Worker
// Scope: /lazestate/ — does NOT handle /lazestate/app/ (app has its own SW)
const CACHE_NAME = 'lazestate-landing-v1';
const STATIC_ASSETS = [
  '/lazestate/',
  '/lazestate/index.html',
  '/lazestate/manifest.json',
  '/lazestate/icons/icon-192x192.png',
  '/lazestate/icons/icon-512x512.png',
  'https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Syne:wght@700;800&family=JetBrains+Mono:wght@400;500&display=swap'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      const local    = STATIC_ASSETS.filter(u => !u.startsWith('http'));
      const external = STATIC_ASSETS.filter(u =>  u.startsWith('http'));
      return cache.addAll(local).then(() =>
        Promise.allSettled(
          external.map(url => fetch(url).then(r => cache.put(url, r)).catch(() => {}))
        )
      );
    }).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);
  // Let the app's own SW handle everything under /lazestate/app/
  if (url.pathname.startsWith('/lazestate/app/')) return;

  event.respondWith(
    caches.match(event.request).then(cached => {
      if (cached) return cached;
      return fetch(event.request).then(response => {
        if (!response || response.status !== 200 || response.type === 'opaque') return response;
        const clone = response.clone();
        caches.open(CACHE_NAME).then(c => c.put(event.request, clone));
        return response;
      }).catch(() => caches.match('/lazestate/index.html'));
    })
  );
});
