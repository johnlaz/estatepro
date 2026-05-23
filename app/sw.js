// LazEstate App Service Worker
// Scope: /lazestate/app/
const CACHE_NAME = 'lazestate-app-v3';
const STATIC_ASSETS = [
  '/lazestate/app/',
  '/lazestate/app/index.html',
  '/lazestate/app/manifest.json',
  '/lazestate/app/icons/icon-192x192.png',
  '/lazestate/app/icons/icon-512x512.png',
  'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap'
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

  // Pass AI/API requests straight to network — never cache Groq calls
  const isApiCall =
    url.hostname !== location.hostname ||
    url.hostname.includes('api.groq.com') ||
    url.hostname.includes('googleapis') ||
    url.hostname.includes('nominatim') ||
    url.hostname.includes('openstreetmap') ||
    url.pathname.includes('/api/');

  if (isApiCall) return;

  event.respondWith(
    caches.match(event.request).then(cached => {
      if (cached) return cached;
      return fetch(event.request).then(response => {
        if (!response || response.status !== 200 || response.type === 'opaque') return response;
        const clone = response.clone();
        caches.open(CACHE_NAME).then(c => c.put(event.request, clone));
        return response;
      }).catch(() => caches.match('/lazestate/app/index.html'));
    })
  );
});
