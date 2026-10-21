const C='escalapro-v2';
self.addEventListener('install',e=>{self.skipWaiting()});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==C).map(k=>caches.delete(k)))).then(()=>self.clients.claim()))});
self.addEventListener('fetch',e=>{const r=e.request;if(r.method!=='GET')return;
 e.respondWith(fetch(r).then(x=>{if(x&&x.ok&&x.type!=='opaque'){const c=x.clone();caches.open(C).then(k=>k.put(r,c)).catch(()=>{})}return x}).catch(()=>caches.match(r).then(m=>m||(r.mode==='navigate'?caches.match(self.registration.scope):undefined)||Response.error())))});
