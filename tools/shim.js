(()=>{const N=async()=>null;
const SBU='https://hofrthndlstofytlapzk.supabase.co',KEY='sb_publishable_Hmstttzx95SEN24Olsuk0g_AuPGnkX7',SB=SBU+'/rest/v1/pub?select=id,j&order=id',CDN='https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.49.4/dist/umd/supabase.min.js',VSB=new URL('vendor/supabase.min.js',location.href).href;
const lg=k=>{try{return localStorage.getItem(k)}catch(e){return null}},ls=(k,v)=>{try{v==null?localStorage.removeItem(k):localStorage.setItem(k,v)}catch(e){}};
const toObj=a=>{const o={};a.forEach(x=>o[x.id]={j:x.j});return o};
/* modo aberto (padrão): leitura anônima do Supabase, com a cópia pub.json como reserva */
const live=async()=>{const r=await fetch(SB,{headers:{apikey:KEY,Accept:'application/json'},cache:'no-store'});if(!r.ok)throw new Error('sb '+r.status);const a=await r.json();if(!Array.isArray(a)||!a.length)throw new Error('vazio');return toObj(a)};
const snap=async()=>{const r=await fetch('pub.json?t='+Date.now(),{cache:'no-store'});if(!r.ok)throw new Error('pub');return r.json()};
/* configuração pública: login obrigatório e contato da facilitadora */
let CFG={};try{CFG=JSON.parse(lg('fv-cfg')||'{}')}catch(e){}
async function cfgLoad(){try{const r=await fetch(SBU+'/rest/v1/config?select=chave,valor',{headers:{apikey:KEY,Accept:'application/json'},cache:'no-store'});if(r.ok){const a=await r.json();const o={};(a||[]).forEach(x=>o[x.chave]=x.valor);CFG=o;ls('fv-cfg',JSON.stringify(o))}}catch(e){}return CFG}
window.__FVCFG=()=>CFG;
/* modo com login */
let sb=null,okRes;const ready=new Promise(r=>okRes=r);
const keep=()=>lg('fv-keep')!=='0';
const store={getItem:k=>{try{return(keep()?localStorage:sessionStorage).getItem(k)}catch(e){return null}},setItem:(k,v)=>{try{(keep()?localStorage:sessionStorage).setItem(k,v)}catch(e){}},removeItem:k=>{try{localStorage.removeItem(k);sessionStorage.removeItem(k)}catch(e){}}};
const ld=u=>new Promise((ok,no)=>{if(window.supabase)return ok();const s=document.createElement('script');s.src=u;if(u==CDN)s.crossOrigin='anonymous';s.onload=()=>window.supabase?ok():no(new Error('lib'));s.onerror=()=>no(new Error('lib'));document.head.appendChild(s)}),loadJs=()=>ld(VSB).catch(()=>ld(CDN));
const css=`#fvl{position:fixed;inset:0;z-index:2147483000;background:radial-gradient(900px 420px at 50% -120px,rgba(0,205,211,.16),transparent 70%),#070D18;display:flex;align-items:center;justify-content:center;padding:16px;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,sans-serif;color:#fff;overflow:auto}
#fvl form{width:100%;max-width:360px;background:#111E33;border:1px solid #2A3D5A;border-radius:18px;padding:24px;display:flex;flex-direction:column;gap:12px}
#fvl h1{font-size:1.4rem;margin:0;letter-spacing:.16em}#fvl p{margin:0;color:#A2B1C4;font-size:.9rem;line-height:1.45}
#fvl input[type=email],#fvl input[type=password]{font:inherit;font-size:16px;padding:12px;border-radius:10px;border:1px solid #2A3D5A;background:#070D18;color:#fff}
#fvl label.k{display:flex;align-items:center;gap:10px;font-size:.92rem;color:#C8D2DF;cursor:pointer}#fvl label.k input{width:20px;height:20px;accent-color:#00CDD3}
#fvl button{font:inherit;font-weight:700;padding:12px;border-radius:10px;border:0;background:#00CDD3;color:#04252C;cursor:pointer}
#fvl button.l{background:transparent;color:#00CDD3;font-weight:600;padding:4px}#fvl .er{color:#ff8a8a;min-height:1em;font-size:.88rem}#fvl a{color:#00CDD3}`;
let box=null;
const LOGO='<svg width="52" height="52" viewBox="0 0 100 100" aria-hidden="true"><rect width="100" height="100" rx="24" fill="#00CDD3"/><g transform="translate(11 8) scale(.78)"><path d="M50 6C58 25 79 35 79 60C79 79 66 93 50 93C34 93 21 79 21 60C21 46 29 37 37 29C38 42 43 50 50 53C46 37 45 21 50 6Z" fill="#070D18"/><path d="M41 50h21v7H49v6h11v7H49v13h-8z" fill="#00CDD3"/></g></svg>';
const head=LOGO+'<h1>FERVOR</h1>';
function ui(h){if(!box){const s=document.createElement('style');s.textContent=css;document.head.appendChild(s);box=document.createElement('div');box.id='fvl';document.body.appendChild(box)}box.innerHTML=h;box.hidden=false;const i=box.querySelector('input:not([type=checkbox])');if(i)setTimeout(()=>i.focus(),60)}
const hide=()=>{if(box)box.hidden=true};
const wa=()=>{const n=String(CFG.whats_contato||'').replace(/\D/g,'');return n?'https://wa.me/'+(n.length<=11?'55'+n:n):''};
function loginForm(msg){ui(`<form id="fvf">${head}<p>Entre com o e-mail e a senha que você recebeu da liderança.</p><input id="fve" type="email" autocomplete="username" placeholder="E-mail" required><input id="fvp" type="password" autocomplete="current-password" placeholder="Senha" required><label class="k"><input type="checkbox" id="fvk"${keep()?' checked':''}>Manter conectado neste aparelho</label><div class="er">${msg||''}</div><button type="submit">Entrar</button><button type="button" class="l" id="fvr">Esqueci minha senha</button><button type="button" class="l" style="font-size:.78rem;color:#8FA1B8;font-weight:400" onclick="window.privD&&privD()">Como usamos seus dados</button></form>`);
 box.querySelector('#fvr').onclick=()=>{const w=wa(),nm=String(CFG.nome_contato||'a facilitadora');ui(`<form>${head}<p>Para receber uma nova senha temporária, fale com ${nm.replace(/</g,'')}.</p>${w?`<a href="${w}?text=${encodeURIComponent('Olá! Esqueci minha senha do Fervor. Pode me mandar uma nova senha temporária?')}" target="_blank" rel="noopener" style="text-align:center;font-weight:700;padding:12px;border-radius:10px;background:#25D366;color:#04120a;text-decoration:none">Chamar no WhatsApp</a>`:''}<button type="button" class="l" id="fvv">Voltar</button></form>`);box.querySelector('#fvv').onclick=()=>loginForm()};
 box.querySelector('#fvf').onsubmit=async e=>{e.preventDefault();const er=box.querySelector('.er');er.textContent='Entrando…';ls('fv-keep',box.querySelector('#fvk').checked?'1':'0');
  const {error}=await sb.auth.signInWithPassword({email:box.querySelector('#fve').value.trim(),password:box.querySelector('#fvp').value});
  if(error){er.textContent=/invalid/i.test(error.message)?'E-mail ou senha incorretos.':'Não foi possível entrar: '+error.message;return}check()}}
function pwFirst(){ui(`<form id="fvf">${head}<p><b style="color:#fff">Bem-vindo(a)!</b> Este é o seu primeiro acesso. Crie agora uma senha só sua, diferente da que você recebeu.</p><input id="fvp" type="password" autocomplete="new-password" placeholder="Nova senha (mín. 8 caracteres)" minlength="8" required><input id="fvq" type="password" autocomplete="new-password" placeholder="Repita a nova senha" minlength="8" required><div class="er"></div><button type="submit">Salvar e entrar</button><button type="button" class="l" id="fvo">Sair</button></form>`);
 box.querySelector('#fvo').onclick=async()=>{await sb.auth.signOut();loginForm()};
 box.querySelector('#fvf').onsubmit=async e=>{e.preventDefault();const a=box.querySelector('#fvp').value,b=box.querySelector('#fvq').value,er=box.querySelector('.er');
  if(a.length<8){er.textContent='Use pelo menos 8 caracteres.';return}if(a!==b){er.textContent='As senhas não conferem.';return}er.textContent='Salvando…';
  const {error}=await sb.auth.updateUser({password:a,data:{pw_ok:true}});if(error){er.textContent=/same|different/i.test(error.message)?'A nova senha precisa ser diferente da atual.':'Não foi possível salvar: '+error.message;return}check()}}
async function check(){let s=null;try{s=(await sb.auth.getSession()).data.session}catch(e){}
 if(!s){loginForm();return}
 if(!(s.user.user_metadata||{}).pw_ok&&navigator.onLine){pwFirst();return}
 let m=null;try{const r=await sb.from('membros').select('*').eq('user_id',s.user.id).maybeSingle();if(r.error)throw r.error;m=r.data;if(m)ls('fv-me',JSON.stringify(m))}catch(e){try{const c=JSON.parse(lg('fv-me')||'null');if(c&&c.user_id==s.user.id)m=c}catch(x){}}
 if(!m||m.ativo===false){if(navigator.onLine){let adm=false;try{adm=(await sb.rpc('is_admin')).data===true}catch(e){}if(!adm){await sb.auth.signOut();loginForm('Seu acesso não está ativo. Fale com a liderança.');return}}}
 window.__FVME=m;window.__SBB=sb;hide();okRes(true)}
window.fvSair=async()=>{try{await sb.auth.signOut()}catch(e){}ls('fv-me',null);try{localStorage.removeItem('rep.band')}catch(e){}location.reload()};
async function start(){await cfgLoad();if(CFG.login_banda!==true){okRes(false);return}
 try{await loadJs()}catch(e){ui(`<form>${head}<p>Sem conexão para entrar. Verifique a internet e recarregue a página.</p></form>`);return}
 sb=window.supabase.createClient(SBU,KEY,{auth:{persistSession:true,autoRefreshToken:true,storage:store,storageKey:'fv-band-auth'}});
 const go=()=>check().catch(()=>loginForm('Sem conexão com o servidor. Tente de novo.'));if(document.body)go();else document.addEventListener('DOMContentLoaded',go)}
start();
const pub=async()=>{const locked=await ready;let o;
 if(locked){let all=[],f=0;for(;;){const {data,error}=await sb.from('pub').select('id,j').order('id').range(f,f+999);if(error)throw error;all=all.concat(data);if(data.length<1000)break;f+=1000}o=toObj(all)}
 else{try{o=await live()}catch(e){o=await snap()}}
 return Object.keys(o).map(id=>({id,exists:true,data:()=>JSON.parse(JSON.stringify(o[id]))}))};
const coll=p=>({get:async()=>({docs:p=='pub'?await pub():[]}),doc:id=>({get:async()=>{if(p=='pub'){const d=(await pub()).find(x=>x.id==id);return d||{id,exists:false,data:()=>undefined}}return{id,exists:false,data:()=>undefined}},set:N,update:N,delete:N}),add:N});
const db={collection:coll,doc:p=>{const i=p.lastIndexOf('/');return coll(p.slice(0,i)).doc(p.slice(i+1))}};
const user={isOwner:async()=>false,canEdit:async()=>false,id:async()=>(window.__FVME&&window.__FVME.user_id)||'banda',profiles:async()=>({})};
window.__B6SITE=1;window.claude={use:async n=>{await ready;return n=='db'?db:n=='user'?user:null}};})();
