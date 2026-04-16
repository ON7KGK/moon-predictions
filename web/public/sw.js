// ════════════════════════════════════════════════════════════════════
// Service Worker minimal — requis pour que Chrome/Edge proposent
// "Installer Moon Predictions" dans la barre d'adresse.
// Pas de caching offline actif (pass-through fetch) — simple mais
// suffisant pour l'installabilité PWA.
// ════════════════════════════════════════════════════════════════════

self.addEventListener("install", (e) => {
  self.skipWaiting();
});

self.addEventListener("activate", (e) => {
  e.waitUntil(self.clients.claim());
});

self.addEventListener("fetch", (e) => {
  // Laisser passer les requêtes sans interférer (online-only).
  // Pour activer l'offline plus tard : cache les assets statiques ici.
});
