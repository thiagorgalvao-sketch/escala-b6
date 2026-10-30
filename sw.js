// Escala B6 - service worker do site da banda
// Página e dados: rede primeiro, cópia salva quando estiver sem internet.
// Áudios (media/): não passam por aqui; o app guarda os do culto no aparelho (IndexedDB).
const C='escalab6-v8',SHELL=['./','index.html','pub.json','manifest.webmanifest','icon-180.png','icon-192.png','icon-512.png','admin/','admin/index.html'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(C).then(c=>c.addAll(SHELL)).catch(()=>{}));self.skipWaiting()});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==C).map(k=>caches.delete(k)))).then(()=>self.clients.claim()))});
self.addEventListener('fetch',e=>{const r=e.request;if(r.method!=='GET')return;const u=new URL(r.url);
 if(u.host==='cdn.jsdelivr.net'){e.respondWith(caches.open(C).then(c=>c.match(r).then(m=>m||fetch(r).then(x=>{if(x&&(x.ok||x.type==='opaque'))c.put(r,x.clone());return x}))));return}
 if(u.origin!==location.origin||u.pathname.includes('/media/')||r.headers.has('range'))return;
 const key=u.origin+u.pathname;
 e.respondWith(fetch(r).then(x=>{if(x&&x.status===200&&x.type==='basic'){const c=x.clone();caches.open(C).then(k=>k.put(key,c)).catch(()=>{})}return x})
  .catch(()=>caches.match(key,{ignoreSearch:true}).then(m=>m||(r.mode==='navigate'?caches.match('index.html',{ignoreSearch:true}).then(x=>x||caches.match('./')):undefined)||Response.error())))});

// avisos no celular (notificações de repertório publicado)
self.addEventListener('push',e=>{let d={};try{d=e.data?e.data.json():{}}catch(x){d={title:'Escala B6',body:e.data?e.data.text():''}}
 e.waitUntil(self.registration.showNotification(d.title||'Escala B6',{body:d.body||'',icon:'icon-192.png',badge:'icon-192.png',tag:d.tag||'escala-b6',renotify:true,data:{url:d.url||self.registration.scope}}))});
self.addEventListener('notificationclick',e=>{e.notification.close();const u=(e.notification.data&&e.notification.data.url)||self.registration.scope;
 e.waitUntil(clients.matchAll({type:'window',includeUncontrolled:true}).then(cs=>{for(const c of cs){if(c.url.startsWith(self.registration.scope)&&!c.url.includes('/admin/')&&'focus' in c){return c.focus()}}return clients.openWindow(u)}))});
