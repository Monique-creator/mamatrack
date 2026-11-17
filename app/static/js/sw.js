const CACHE = "mamatrack-field-v2";
const OFFLINE_PAGE = "/static/offline.html";
const SHELL = [
  "/field",
  OFFLINE_PAGE,
  "/static/css/base.css",
  "/static/css/components.css",
  "/static/css/pages.css",
  "/static/css/field.css",
  "/static/css/responsive.css",
  "/static/js/offline.js",
  "/static/img/logo.svg",
];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(SHELL)).catch(() => {}));
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(caches.keys().then((keys) =>
    Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))));
  self.clients.claim();
});

function saveCopy(request, response) {
  if (response.ok && !response.redirected) {
    const copy = response.clone();
    caches.open(CACHE).then((cache) => cache.put(request, copy));
  }
  return response;
}

// Network first. Offline, the CHW page and its files come from the cache, and any
// other page opened without network shows a short offline notice instead of an error.
self.addEventListener("fetch", (event) => {
  const request = event.request;
  const url = new URL(request.url);
  if (request.method !== "GET" || url.pathname.startsWith("/api/")) return;

  const cacheable = url.pathname === "/field" || url.pathname.startsWith("/static/");
  if (!cacheable && request.mode !== "navigate") return;

  event.respondWith(
    fetch(request)
      .then((response) => (cacheable ? saveCopy(request, response) : response))
      .catch(async () => (await caches.match(request)) || caches.match(OFFLINE_PAGE))
  );
});