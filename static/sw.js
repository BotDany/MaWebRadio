// Service Worker pour les notifications en arrière-plan
const CACHE_NAME = 'radio-player-v1';
const urlsToCache = [
  '/',
  '/static/manifest.json',
  '/static/icon-192x192.png'
];

// Installation du Service Worker
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        return cache.addAll(urlsToCache);
      })
  );
});

// Activation du Service Worker
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

// Gestion des notifications
self.addEventListener('notificationclick', event => {
  event.notification.close();
  
  if (event.action === 'play') {
    // Envoyer un message à la page pour jouer
    event.waitUntil(
      clients.matchAll().then(clientList => {
        for (const client of clientList) {
          if (client.url === '/' && 'focus' in client) {
            return client.focus().then(client => {
              client.postMessage({ action: 'play' });
            });
          }
        }
        // Si aucune page n'est ouverte, en ouvrir une nouvelle
        if (clients.openWindow) {
          return clients.openWindow('/');
        }
      })
    );
  } else if (event.action === 'pause') {
    // Envoyer un message à la page pour mettre en pause
    event.waitUntil(
      clients.matchAll().then(clientList => {
        for (const client of clientList) {
          if (client.url === '/' && 'focus' in client) {
            return client.focus().then(client => {
              client.postMessage({ action: 'pause' });
            });
          }
        }
      })
    );
  } else if (event.action === 'stop') {
    // Envoyer un message à la page pour arrêter
    event.waitUntil(
      clients.matchAll().then(clientList => {
        for (const client of clientList) {
          if (client.url === '/' && 'focus' in client) {
            return client.focus().then(client => {
              client.postMessage({ action: 'stop' });
            });
          }
        }
      })
    );
  } else {
    // Clic simple sur la notification - focus sur la page
    event.waitUntil(
      clients.matchAll().then(clientList => {
        for (const client of clientList) {
          if (client.url === '/' && 'focus' in client) {
            return client.focus();
          }
        }
        if (clients.openWindow) {
          return clients.openWindow('/');
        }
      })
    );
  }
});

// Gestion de la fermeture des notifications
self.addEventListener('notificationclose', event => {
  console.log('Notification fermée:', event.notification.tag);
});

// Intercepter les requêtes réseau
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Cache hit - return response
        if (response) {
          return response;
        }
        return fetch(event.request);
      }
    )
  );
});
