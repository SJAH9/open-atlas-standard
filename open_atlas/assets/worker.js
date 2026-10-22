/* Project-local offline shell. No third-party requests, audio, identity or tracking. */
const CACHE='open-atlas-0.1';const FILES=['./','index.html','atlas.css','atlas.js','icon.svg','data.json','equirectangular.svg','equal-area.svg','manifest.webmanifest','observations.csv','geometry.geojson','build-manifest.json'];
const key=CACHE+':'+self.registration.scope;
self.addEventListener('install',e=>{e.waitUntil(caches.open(key).then(c=>c.addAll(FILES)).then(()=>self.skipWaiting()))});
self.addEventListener('activate',e=>{e.waitUntil(self.clients.claim())});
self.addEventListener('fetch',e=>{if(e.request.method!=='GET'||!e.request.url.startsWith(self.registration.scope)||e.request.headers.has('Authorization'))return;const relative=new URL(e.request.url).pathname.slice(new URL(self.registration.scope).pathname.length);if(!FILES.includes(relative)&&relative!=='')return;e.respondWith(fetch(e.request).then(r=>{if(r.ok){const copy=r.clone();caches.open(key).then(c=>c.put(e.request,copy))}return r}).catch(()=>caches.match(e.request,{ignoreSearch:true})))});
