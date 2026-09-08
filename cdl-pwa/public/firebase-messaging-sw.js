// firebase-messaging-sw.js
// This file acts as BOTH the PWA service worker (caching) and the Firebase
// background-message handler. It must live at the site root.
//
// ⚠️  IMPORTANT: Copy your Firebase project config values below.
//     They are safe to commit — they are not secret keys.

importScripts('https://www.gstatic.com/firebasejs/10.12.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.12.0/firebase-messaging-compat.js');

firebase.initializeApp({
  apiKey:            'REPLACE_WITH_FIREBASE_API_KEY',
  authDomain:        'REPLACE_WITH_AUTH_DOMAIN',
  projectId:         'REPLACE_WITH_PROJECT_ID',
  storageBucket:     'REPLACE_WITH_STORAGE_BUCKET',
  messagingSenderId: 'REPLACE_WITH_MESSAGING_SENDER_ID',
  appId:             'REPLACE_WITH_APP_ID',
});

const messaging = firebase.messaging();

// Background push notifications (app is closed or in background)
messaging.onBackgroundMessage((payload) => {
  const title = payload.notification?.title ?? 'Road Test Alert';
  const body  = payload.notification?.body  ?? '';
  self.registration.showNotification(title, {
    body,
    icon:      '/icon-192.png',
    badge:     '/icon-192.png',
    tag:       'cdl-alert',
    renotify:  true,
  });
});

// ---------------------------------------------------------------
// PWA caching (offline shell)
// ---------------------------------------------------------------
const CACHE = 'cdl-v1';
const SHELL = ['/', '/index.html'];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)));
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (e) => {
  if (e.request.method !== 'GET') return;
  e.respondWith(
    caches.match(e.request).then((cached) => cached ?? fetch(e.request))
  );
});
