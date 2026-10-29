// Supabase falso, em memória + localStorage (só para testes locais)
(()=>{const raw=(()=>{try{return Object.getOwnPropertyDescriptor(Window.prototype,'localStorage')?null:null}catch(e){return null}})();
const LSr=window.localStorage;const K='__stubdb';
const D=()=>JSON.parse(LSr.getItem(K)||'{}');const W=d=>LSr.setItem(K,JSON.stringify(d));
function tb(n){const d=D();return d[n]||[]}
function put(n,rows){const d=D();d[n]=rows;W(d)}
const uid=()=>([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g,c=>(c^Math.random()*16>>c/4).toString(16));
const PK={membros:['id'],disponibilidade:['membro_id','culto_id'],config:['chave'],pub:['id'],team:['id'],admins:['user_id']};
function Q(t){let op='select',payload=null,flt=[],cols='*',rng=null,one=0,maybe=0;const api={
 select:c=>{cols=c||'*';return api},eq:(k,v)=>{flt.push([k,v]);return api},in:(k,v)=>{flt.push([k,v,'in']);return api},order:()=>api,range:(a,b)=>{rng=[a,b];return api},
 maybeSingle:()=>{maybe=1;return api},single:()=>{one=1;return api},
 insert:o=>{op='insert';payload=o;return api},update:o=>{op='update';payload=o;return api},upsert:o=>{op='upsert';payload=o;return api},delete:()=>{op='delete';return api},
 then:(res,rej)=>Promise.resolve().then(run).then(res,rej)};
 const match=r=>flt.every(([k,v,m])=>m=='in'?v.includes(r[k]):r[k]==v);
 function run(){let rows=tb(t);const pk=PK[t]||['id'];
  if(op=='insert'||op=='upsert'){const arr=[].concat(payload).map(o=>Object.assign({},o));for(const o of arr){if(t=='membros'&&!o.id)o.id=uid();const i=rows.findIndex(r=>pk.every(k=>r[k]==o[k]));if(op=='insert'&&t=='membros'&&rows.some(r=>(r.nome||'').toLowerCase()==(o.nome||'').toLowerCase()))return{data:null,error:{message:'duplicate key value violates unique constraint'}};if(i>=0)rows[i]=Object.assign(rows[i],o);else rows.push(Object.assign({ativo:true,fixo:true,funcoes:[]},t=='membros'?{}:{},o))}put(t,rows);return{data:arr,error:null}}
  if(op=='update'){rows.forEach(r=>{if(match(r))Object.assign(r,payload)});put(t,rows);return{data:null,error:null}}
  if(op=='delete'){put(t,rows.filter(r=>!match(r)));return{data:null,error:null}}
  let out=rows.filter(match);if(rng)out=out.slice(rng[0],rng[1]+1);
  if(/membros\(nome\)/.test(cols)){const M=tb('membros');out=out.map(r=>Object.assign({},r,{membros:{nome:(M.find(m=>m.id==r.membro_id)||{}).nome}}))}
  if(one||maybe)return{data:out[0]||null,error:null};return{data:out,error:null}}
 return api}
let L=[];const SK='sb-sess';
const sess=()=>{try{return JSON.parse(LSr.getItem(SK)||sessionStorage.getItem(SK)||'null')}catch(e){return null}};
function createClient(u,k,o){const st=(o&&o.auth&&o.auth.storage)||null;const key=(o&&o.auth&&o.auth.storageKey)||SK;
 const gs=()=>{try{return JSON.parse((st?st.getItem(key):LSr.getItem(key))||'null')}catch(e){return null}};const ss=v=>{if(st){v?st.setItem(key,JSON.stringify(v)):st.removeItem(key)}else{v?LSr.setItem(key,JSON.stringify(v)):LSr.removeItem(key)}};
 const users=()=>D().users||[];const setUsers=a=>{const d=D();d.users=a;W(d)};
 return{auth:{getSession:async()=>({data:{session:gs()}}),getUser:async()=>({data:{user:(gs()||{}).user||null}}),onAuthStateChange:f=>{L.push(f);return{data:{subscription:{unsubscribe(){}}}}},
  signInWithPassword:async({email,password})=>{const u=users().find(x=>x.email==email&&x.password==password);if(!u)return{error:{message:'Invalid login credentials'}};ss({user:{id:u.id,email:u.email,user_metadata:u.meta||{}}});return{error:null}},
  signOut:async()=>{ss(null);return{error:null}},
  updateUser:async({password,data})=>{const s=gs();if(!s)return{error:{message:'no session'}};const a=users();const u=a.find(x=>x.id==s.user.id);if(password){if(u.password==password)return{error:{message:'New password should be different from the old password.'}};u.password=password}if(data){u.meta=Object.assign(u.meta||{},data);s.user.user_metadata=u.meta;ss(s)}setUsers(a);return{data:{user:s.user},error:null}},
  resetPasswordForEmail:async()=>({error:null}),
  mfa:{getAuthenticatorAssuranceLevel:async()=>({data:{currentLevel:'aal1',nextLevel:'aal1'}}),listFactors:async()=>({data:{all:[],totp:[]}})}},
 from:Q,
 rpc:async n=>{const s=gs();const adm=s&&tb('admins').some(a=>a.user_id==s.user.id);if(n=='is_admin')return{data:!!adm,error:null};if(n=='total_avisos')return{data:0,error:null};return{data:null,error:null}},
 functions:{invoke:async(n,{body})=>{if(n!='gerenciar-acesso')return{data:{ok:true},error:null};if(body.acao=='excluir_minha_conta'){const ss=gs();const M=tb('membros');const m=M.find(x=>x.user_id==ss.user.id);if(m){Object.assign(m,{email:null,whatsapp:null,instagram:null,foto_url:null,ativo:false,user_id:null});put('membros',M);put('disponibilidade',tb('disponibilidade').filter(d=>d.membro_id!=m.id))}setUsers(users().filter(u=>u.id!=ss.user.id));return{data:{ok:true},error:null}}const M=tb('membros'),m=M.find(x=>x.id==body.membro_id);const a=users();
  if(body.acao=='criar'){const senha='Louvor-'+String(Math.floor(Math.random()*1e4)).padStart(4,'0'),id=uid();a.push({id,email:m.email,password:senha,meta:{pw_ok:false}});setUsers(a);m.user_id=id;put('membros',M);return{data:{ok:true,email:m.email,senha},error:null}}
  if(body.acao=='resetar'){const u=a.find(x=>x.id==m.user_id);u.password='Altar-1234';u.meta.pw_ok=false;setUsers(a);return{data:{ok:true,email:u.email,senha:'Altar-1234'},error:null}}
  if(body.acao=='remover'){setUsers(a.filter(x=>x.id!=m.user_id));m.user_id=null;put('membros',M);return{data:{ok:true},error:null}}}},
 storage:{from:()=>({upload:async()=>({error:null}),getPublicUrl:p=>({data:{publicUrl:'data:image/svg+xml,'+encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"><rect width="10" height="10" fill="#f80"/></svg>')}}),remove:async()=>({error:null})})}}}
window.supabase={createClient};window.__stubD=D;})();
