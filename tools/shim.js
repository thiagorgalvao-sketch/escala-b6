(()=>{const N=async()=>null;
const pub=async()=>{const r=await fetch('pub.json?t='+Date.now(),{cache:'no-store'});if(!r.ok)throw new Error('pub');const o=await r.json();return Object.keys(o).map(id=>({id,exists:true,data:()=>JSON.parse(JSON.stringify(o[id]))}))};
const coll=p=>({get:async()=>({docs:p=='pub'?await pub():[]}),doc:id=>({get:async()=>{if(p=='pub'){const d=(await pub()).find(x=>x.id==id);return d||{id,exists:false,data:()=>undefined}}return{id,exists:false,data:()=>undefined}},set:N,update:N,delete:N}),add:N});
const db={collection:coll,doc:p=>{const i=p.lastIndexOf('/');return coll(p.slice(0,i)).doc(p.slice(i+1))}};
const user={isOwner:async()=>false,canEdit:async()=>false,id:async()=>'banda',profiles:async()=>({})};
window.__B6SITE=1;window.claude={use:async n=>n=='db'?db:n=='user'?user:null};})();
