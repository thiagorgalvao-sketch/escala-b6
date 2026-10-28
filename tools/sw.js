// Escala B6 - service worker do site da banda
// Página e dados: rede primeiro, cópia salva quando estiver sem internet.
// Áudios (media/): não passam por aqui; o app guarda os do culto no aparelho (IndexedDB).
const C='escalab6-v5',SHELL=['./','index.html','pub.json','manifest.webmanifest','icon-180.png','icon-192.png','icon-512.png'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(C).then(c=>c.addAll(SHELL)).catch(()=>{}));self.skipWaiting()});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==C).map(k=>caches.delete(k)))).then(()=>self.clients.claim()))});
self.addEventListener('fetch',e=>{const r=e.request;if(r.method!=='GET')return;const u=new URL(r.url);
 if(u.origin!==location.origin||u.pathname.includes('/media/')||r.headers.has('range'))return;
 const key=u.origin+u.pathname;
 e.respondWith(fetch(r).then(x=>{if(x&&x.status===200&&x.type==='basic'){const c=x.clone();caches.open(C).then(k=>k.put(key,c)).catch(()=>{})}return x})
  .catch(()=>caches.match(key,{ignoreSearch:true}).then(m=>m||(r.mode==='navigate'?caches.match('index.html',{ignoreSearch:true}).then(x=>x||caches.match('./')):undefined)||Response.error())))});
