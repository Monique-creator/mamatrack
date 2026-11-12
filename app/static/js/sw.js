const CACHE = "mamatrack-field-v1";
const SHELL = [
  "/field",
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
});

// Network first, fall back to the last copy so the CHW page still opens offline.
self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  if (event.request.method !== "GET" || url.pathname.startsWith("/api/")) return;
  if (url.pathname !== "/field" && !url.pathname.startsWith("/static/")) return;

  event.respondWith(
    fetch(event.request)
      .then((response) => {
        if (response.ok && !response.redirected) {
          const copy = response.clone();
          caches.open(CACHE).then((cache) => cache.put(event.request, copy));
        }
        return response;
      })
      .catch(() => caches.match(event.request))
  );
});