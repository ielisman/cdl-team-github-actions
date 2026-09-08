import App from './App.svelte'
import './App.css'

// Register unified service worker (PWA caching + Firebase background messages)
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker
      .register('/firebase-messaging-sw.js')
      .then((reg) => console.log('Service worker registered:', reg.scope))
      .catch((err) => console.error('Service worker registration failed:', err))
  })
}

new App({
  target: document.getElementById('root'),
})
