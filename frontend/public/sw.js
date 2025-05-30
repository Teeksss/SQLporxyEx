/**
 * Enterprise SQL Proxy System - Service Worker
 * Created: 2025-05-30 06:38:34 UTC by Teeksss
 * Version: 2.0.0 Final
 */

const CACHE_NAME = 'esp-v2.0.0-2025-05-30-06-38-34';
const API_CACHE_NAME = 'esp-api-v2.0.0';
const STATIC_CACHE_NAME = 'esp-static-v2.0.0';

// Resources to cache on install
const STATIC_RESOURCES = [
  '/',
  '/static/js/bundle.js',
  '/static/css/main.css',
  '/manifest.json',
  '/favicon.ico',
  '/logo192.png',
  '/logo512.png'
];

// API endpoints to cache
const API_CACHE_PATTERNS = [
  /\/api\/v1\/health/,
  /\/api\/v1\/auth\/me/,
  /\/api\/v1\/proxy\/servers/
];

// Resources that should always be fetched from network
const NETWORK_FIRST = [
  /\/api\/v1\/auth\/login/,
  /\/api\/v1\/auth\/logout/,
  /\/api\/v1\/proxy\/execute/,
  /\/api\/v1\/notifications/
];

// Install event - cache static resources
self.addEventListener('install', event => {
  console.log('[SW] Installing Service Worker v2.0.0 by Teeksss');
  
  event.waitUntil(
    caches.open(STATIC_CACHE_NAME)
      .then(cache => {
        console.log('[SW] Caching static resources');
        return cache.addAll(STATIC_RESOURCES);
      })
      .then(() => {
        console.log('[SW] Static resources cached successfully');
        return self.skipWaiting();
      })
      .catch(error => {
        console.error('[SW] Failed to cache static resources:', error);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  console.log('[SW] Activating Service Worker v2.0.0');
  
  event.waitUntil(
    caches.keys()
      .then(cacheNames => {
        return Promise.all(
          cacheNames.map(cacheName => {
            // Delete old cache versions
            if (cacheName !== CACHE_NAME && 
                cacheName !== API_CACHE_NAME && 
                cacheName !== STATIC_CACHE_NAME) {
              console.log('[SW] Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log('[SW] Service Worker activated successfully');
        return self.clients.claim();
      })
      .catch(error => {
        console.error('[SW] Failed to activate Service Worker:', error);
      })
  );
});

// Fetch event - handle all network requests
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }
  
  // Skip chrome-extension requests
  if (url.protocol === 'chrome-extension:') {
    return;
  }
  
  // Handle different request types
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(handleApiRequest(request));
  } else if (url.pathname.startsWith('/static/')) {
    event.respondWith(handleStaticRequest(request));
  } else {
    event.respondWith(handleNavigationRequest(request));
  }
});

// Handle API requests
async function handleApiRequest(request) {
  const url = new URL(request.url);
  
  // Network first for critical endpoints
  if (NETWORK_FIRST.some(pattern => pattern.test(url.pathname))) {
    return handleNetworkFirst(request, API_CACHE_NAME);
  }
  
  // Cache first for cacheable API endpoints
  if (API_CACHE_PATTERNS.some(pattern => pattern.test(url.pathname))) {
    return handleCacheFirst(request, API_CACHE_NAME);
  }
  
  // Default to network only for other API requests
  return fetch(request);
}

// Handle static resource requests
async function handleStaticRequest(request) {
  return handleCacheFirst(request, STATIC_CACHE_NAME);
}

// Handle navigation requests (HTML pages)
async function handleNavigationRequest(request) {
  // For SPA routing, always return index.html from cache or network
  try {
    const cache = await caches.open(STATIC_CACHE_NAME);
    let response = await cache.match('/');
    
    if (!response) {
      response = await fetch('/');
      if (response.ok) {
        cache.put('/', response.clone());
      }
    }
    
    return response;
  } catch (error) {
    console.error('[SW] Failed to handle navigation request:', error);
    return new Response('Offline', { status: 503 });
  }
}

// Cache first strategy
async function handleCacheFirst(request, cacheName) {
  try {
    const cache = await caches.open(cacheName);
    const cachedResponse = await cache.match(request);
    
    if (cachedResponse) {
      // Return cached response and update cache in background
      updateCacheInBackground(request, cache);
      return cachedResponse;
    }
    
    // Not in cache, fetch from network
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    console.error('[SW] Cache first strategy failed:', error);
    return new Response('Network Error', { status: 503 });
  }
}

// Network first strategy
async function handleNetworkFirst(request, cacheName) {
  try {
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    console.error('[SW] Network first failed, trying cache:', error);
    
    // Fallback to cache
    const cache = await caches.open(cacheName);
    const cachedResponse = await cache.match(request);
    
    if (cachedResponse) {
      return cachedResponse;
    }
    
    return new Response('Offline', { status: 503 });
  }
}

// Update cache in background
async function updateCacheInBackground(request, cache) {
  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      cache.put(request, networkResponse.clone());
    }
  } catch (error) {
    // Silently fail background updates
  }
}

// Handle messages from main thread
self.addEventListener('message', event => {
  const { type, payload } = event.data;
  
  switch (type) {
    case 'SKIP_WAITING':
      self.skipWaiting();
      break;
    
    case 'CACHE_API_RESPONSE':
      cacheApiResponse(payload.request, payload.response);
      break;
    
    case 'CLEAR_CACHE':
      clearCache(payload.cacheName);
      break;
    
    case 'GET_CACHE_INFO':
      getCacheInfo().then(info => {
        event.ports[0].postMessage(info);
      });
      break;
    
    default:
      console.warn('[SW] Unknown message type:', type);
  }
});

// Cache API response
async function cacheApiResponse(requestUrl, responseData) {
  try {
    const cache = await caches.open(API_CACHE_NAME);
    const response = new Response(JSON.stringify(responseData), {
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'max-age=300' // 5 minutes
      }
    });
    
    await cache.put(requestUrl, response);
    console.log('[SW] Cached API response:', requestUrl);
  } catch (error) {
    console.error('[SW] Failed to cache API response:', error);
  }
}

// Clear specific cache
async function clearCache(cacheName) {
  try {
    if (cacheName) {
      await caches.delete(cacheName);
      console.log('[SW] Cleared cache:', cacheName);
    } else {
      // Clear all caches
      const cacheNames = await caches.keys();
      await Promise.all(cacheNames.map(name => caches.delete(name)));
      console.log('[SW] Cleared all caches');
    }
  } catch (error) {
    console.error('[SW] Failed to clear cache:', error);
  }
}

// Get cache information
async function getCacheInfo() {
  try {
    const cacheNames = await caches.keys();
    const cacheInfo = {};
    
    for (const cacheName of cacheNames) {
      const cache = await caches.open(cacheName);
      const keys = await cache.keys();
      cacheInfo[cacheName] = {
        size: keys.length,
        urls: keys.map(req => req.url)
      };
    }
    
    return {
      version: '2.0.0',
      caches: cacheInfo,
      timestamp: new Date().toISOString(),
      creator: 'Teeksss'
    };
  } catch (error) {
    console.error('[SW] Failed to get cache info:', error);
    return { error: error.message };
  }
}

// Background sync for offline actions
self.addEventListener('sync', event => {
  console.log('[SW] Background sync triggered:', event.tag);
  
  if (event.tag === 'background-sync') {
    event.waitUntil(doBackgroundSync());
  }
});

// Perform background sync
async function doBackgroundSync() {
  try {
    // Sync any pending offline actions
    console.log('[SW] Performing background sync');
    
    // Example: Sync pending query executions
    // This would be implemented based on your offline strategy
    
  } catch (error) {
    console.error('[SW] Background sync failed:', error);
  }
}

// Push notification handler
self.addEventListener('push', event => {
  console.log('[SW] Push notification received');
  
  const options = {
    body: 'You have new notifications in Enterprise SQL Proxy System',
    icon: '/logo192.png',
    badge: '/logo192.png',
    tag: 'esp-notification',
    data: event.data ? event.data.json() : {},
    actions: [
      {
        action: 'view',
        title: 'View',
        icon: '/icons/view-icon.png'
      },
      {
        action: 'dismiss',
        title: 'Dismiss',
        icon: '/icons/dismiss-icon.png'
      }
    ],
    requireInteraction: true
  };
  
  event.waitUntil(
    self.registration.showNotification('Enterprise SQL Proxy System', options)
  );
});

// Notification click handler
self.addEventListener('notificationclick', event => {
  console.log('[SW] Notification clicked:', event.action);
  
  event.notification.close();
  
  if (event.action === 'view') {
    event.waitUntil(
      clients.openWindow('/')
    );
  }
});

// Error handler
self.addEventListener('error', event => {
  console.error('[SW] Service Worker error:', event.error);
});

// Unhandled rejection handler
self.addEventListener('unhandledrejection', event => {
  console.error('[SW] Unhandled promise rejection:', event.reason);
});

console.log('[SW] Enterprise SQL Proxy System Service Worker v2.0.0 loaded');
console.log('[SW] Created by: Teeksss');
console.log('[SW] Build Date: 2025-05-30 06:38:34 UTC');