const CACHE_NAME = 'mykolaivka-app-cache-v0.2';
const API_CACHE_NAME = 'mykolaivka-api-cache-v1';

const urlsToCache = [
  './',
  './style.css',
  './script.js',
  './ico/android-chrome-192x192.png',
  './ico/android-chrome-512x512.png',
  './ico/apple-touch-icon.png',
  './ico/favicon-16x16.png',
  './ico/favicon-32x32.png',
  './ico/favicon.ico',
  './site.webmanifest'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(urlsToCache);
    })
  );
});

self.addEventListener('message', (event) => {
  if (event.data && event.data.action === 'skipWaiting') {
    self.skipWaiting();
  }
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request).catch(() => caches.match('./'))
    );
    return;
  }

  if (url.hostname === 'raw.githubusercontent.com' || url.pathname.includes('database.json')) {
    event.respondWith(
      caches.open(API_CACHE_NAME).then((cache) => {
        return cache.match(event.request).then((cachedResponse) => {
          const fetchPromise = fetch(event.request, { cache: 'no-store' })
            .then((networkResponse) => {
              cache.put(event.request, networkResponse.clone());
              return networkResponse;
            })
            .catch(() => cachedResponse);
          return cachedResponse || fetchPromise;
        });
      })
    );
    return;
  }

  event.respondWith(
    caches.match(event.request).then((response) => {
      return response || fetch(event.request);
    })
  );
});

self.addEventListener('activate', (event) => {
  const cacheWhitelist = [CACHE_NAME, API_CACHE_NAME];
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (!cacheWhitelist.includes(cacheName)) {
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});
