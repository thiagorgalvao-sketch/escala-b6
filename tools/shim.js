(()=>{const N=async()=>null;
const SB='https://hofrthndlstofytlapzk.supabase.co/rest/v1/pub?select=id,j&order=id',KEY='sb_publishable_Hmstttzx95SEN24Olsuk0g_AuPGnkX7';
const live=async()=>{const r=await fetch(SB,{headers:{apikey:KEY,Accept:'application/json'},cache:'no-store'});if(!r.ok)throw new Error('sb '+r.status);const a=await r.json();if(!Array.isArray(a)||!a.length)throw new Error('vazio');const o={};a.forEach(x=>o[x.id]={j:x.j});return o};
const snap=async()=>{const r=await fetch('pub.json?t='+Date.now(),{cache:'no-store'});if(!r.ok)throw new Error('pub');return r.json()};
const pub=async()=>{let o;try{o=await live()}catch(e){o=await snap()}return Object.keys(o).map(id=>({id,exists:true,data:()=>JSON.parse(JSON.stringify(o[id]))}))};
const coll=p=>({get:async()=>({docs:p=='pub'?await pub():[]}),doc:id=>({get:async()=>{if(p=='pub'){const d=(await pub()).find(x=>x.id==id);return d||{id,exists:false,data:()=>undefined}}return{id,exists:false,data:()=>undefined}},set:N,update:N,delete:N}),add:N});
const db={collection:coll,doc:p=>{const i=p.lastIndexOf('/');return coll(p.slice(0,i)).doc(p.slice(i+1))}};
const user={isOwner:async()=>false,canEdit:async()=>false,id:async()=>'banda',profiles:async()=>({})};
window.__B6SITE=1;window.claude={use:async n=>n=='db'?db:n=='user'?user:null};})();
