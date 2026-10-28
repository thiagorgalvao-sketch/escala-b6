/* Escala B6 · ponte do app com o Supabase (login + banco + arquivos), substitui o ambiente do Claude */
(()=>{
const SBURL='https://hofrthndlstofytlapzk.supabase.co',KEY='sb_publishable_Hmstttzx95SEN24Olsuk0g_AuPGnkX7',BUCKET='midias';
/* dados locais separados da visão da banda (mesmo endereço do site) */
try{const ls=window.localStorage,P='adm:';const W={getItem:k=>ls.getItem(P+k),setItem:(k,v)=>ls.setItem(P+k,v),removeItem:k=>ls.removeItem(P+k),clear:()=>{Object.keys(ls).filter(k=>k.startsWith(P)).forEach(k=>ls.removeItem(k))},key:i=>Object.keys(ls).filter(k=>k.startsWith(P))[i]?.slice(P.length)??null,get length(){return Object.keys(ls).filter(k=>k.startsWith(P)).length}};
 Object.defineProperty(window,'localStorage',{configurable:true,get:()=>W})}catch(e){}
window.__B6SB=1;if(!window.supabase){const f=()=>{document.body.insertAdjacentHTML('beforeend','<div style="position:fixed;inset:0;z-index:2147483000;background:#070D18;color:#fff;display:flex;align-items:center;justify-content:center;padding:24px;text-align:center;font-family:system-ui"><div><b>Sem conexão com o servidor.</b><br><br>Verifique a internet e recarregue a página.</div></div>')};if(document.body)f();else document.addEventListener('DOMContentLoaded',f);return}
const sb=window.supabase.createClient(SBURL,KEY,{auth:{persistSession:true,autoRefreshToken:true,storageKey:'b6-auth'}});
window.__SB=sb;window.__B6SB=1;
const css=`#b6l{position:fixed;inset:0;z-index:2147483000;background:radial-gradient(900px 420px at 50% -120px,rgba(0,205,211,.14),transparent 70%),#070D18;display:flex;align-items:center;justify-content:center;padding:16px;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,sans-serif;color:#fff}
#b6l form{width:100%;max-width:360px;background:#111E33;border:1px solid #2A3D5A;border-radius:18px;padding:24px;display:flex;flex-direction:column;gap:12px}
#b6l h1{font-size:1.35rem;margin:0}#b6l p{margin:0;color:#A2B1C4;font-size:.9rem;line-height:1.4}
#b6l input{font:inherit;font-size:16px;padding:12px;border-radius:10px;border:1px solid #2A3D5A;background:#070D18;color:#fff}
#b6l button{font:inherit;font-weight:700;padding:12px;border-radius:10px;border:0;background:#00CDD3;color:#04252C;cursor:pointer}
#b6l button.l{background:transparent;color:#00CDD3;font-weight:600;padding:4px}#b6l .er{color:#ff8a8a;min-height:1em;font-size:.88rem}
#b6l .ok{color:#7CCEDB;font-size:.88rem}#b6l .bd{width:44px;height:44px;border-radius:50%;border:2px solid #00CDD3;display:grid;place-items:center;font-weight:800}`;
let box=null;
function ui(html){if(!box){const s=document.createElement('style');s.textContent=css;document.head.appendChild(s);box=document.createElement('div');box.id='b6l';document.body.appendChild(box)}box.innerHTML=html;box.hidden=false;const i=box.querySelector('input');if(i)setTimeout(()=>i.focus(),50)}
const hide=()=>{if(box)box.hidden=true};
const head='<div class="bd">B6</div><h1>Escala B6 · Administração</h1>';
let okRes;const ready=new Promise(r=>okRes=r);
async function isAdm(){const {data,error}=await sb.rpc('is_admin');return !error&&data===true}
function loginForm(msg){ui(`<form id="b6f">${head}<p>Entre com o seu e-mail e senha.</p><input id="b6e" type="email" autocomplete="username" placeholder="E-mail" required><input id="b6p" type="password" autocomplete="current-password" placeholder="Senha" required><div class="er">${msg||''}</div><button type="submit">Entrar</button><button type="button" class="l" id="b6r">Esqueci minha senha</button></form>`);
 box.querySelector('#b6f').onsubmit=async e=>{e.preventDefault();const er=box.querySelector('.er');er.textContent='Entrando…';
  const {error}=await sb.auth.signInWithPassword({email:box.querySelector('#b6e').value.trim(),password:box.querySelector('#b6p').value});
  if(error){er.textContent=/invalid/i.test(error.message)?'E-mail ou senha incorretos.':'Não foi possível entrar: '+error.message;return}check()};
 box.querySelector('#b6r').onclick=()=>resetForm(box.querySelector('#b6e').value)}
function resetForm(em){ui(`<form id="b6f">${head}<p>Vamos enviar um link para você criar uma nova senha.</p><input id="b6e" type="email" placeholder="E-mail" value="${(em||'').replace(/"/g,'')}" required><div class="er"></div><button type="submit">Enviar link</button><button type="button" class="l" id="b6v">Voltar</button></form>`);
 box.querySelector('#b6v').onclick=()=>loginForm();
 box.querySelector('#b6f').onsubmit=async e=>{e.preventDefault();const er=box.querySelector('.er');er.textContent='Enviando…';
  const {error}=await sb.auth.resetPasswordForEmail(box.querySelector('#b6e').value.trim(),{redirectTo:location.origin+location.pathname});
  er.className=error?'er':'ok';er.textContent=error?'Não foi possível enviar: '+error.message:'Se o e-mail estiver cadastrado, o link chega em alguns minutos. Confira também o spam.'}}
function pwForm(title,after){ui(`<form id="b6f">${head}<p>${title}</p><input id="b6p" type="password" autocomplete="new-password" placeholder="Nova senha (mín. 8 caracteres)" minlength="8" required><input id="b6q" type="password" autocomplete="new-password" placeholder="Repita a nova senha" minlength="8" required><div class="er"></div><button type="submit">Salvar senha</button>${after?'<button type="button" class="l" id="b6v">Cancelar</button>':''}</form>`);
 if(after)box.querySelector('#b6v').onclick=()=>{hide();after()};
 box.querySelector('#b6f').onsubmit=async e=>{e.preventDefault();const a=box.querySelector('#b6p').value,b=box.querySelector('#b6q').value,er=box.querySelector('.er');
  if(a!==b){er.textContent='As senhas não conferem.';return}er.textContent='Salvando…';const {error}=await sb.auth.updateUser({password:a});
  if(error){er.textContent='Não foi possível salvar: '+error.message;return}hide();if(after)after();else check();try{toast('Senha alterada')}catch(x){}}}
let recovering=false;
sb.auth.onAuthStateChange((ev)=>{if(ev==='PASSWORD_RECOVERY'){recovering=true;pwForm('Crie a sua nova senha.')}});
async function check(){if(recovering)return;const {data:{session}}=await sb.auth.getSession();if(!session){loginForm();return}
 if(!(await isAdm())){await sb.auth.signOut();loginForm('Esta conta não tem acesso de administrador.');return}
 hide();okRes(session)}
window.b6Conta=async()=>{const {data:{session}}=await sb.auth.getSession();const em=session&&session.user.email||'';
 try{dlg.close()}catch(e){}
 ui(`<form>${head}<p>Conectado como <b style="color:#fff">${em.replace(/</g,'')}</b></p><button type="button" id="b6s">Trocar senha</button><button type="button" class="l" id="b6o" style="color:#ff8a8a">Sair deste aparelho</button><button type="button" class="l" id="b6v">Voltar ao app</button></form>`);
 box.querySelector('#b6v').onclick=hide;box.querySelector('#b6s').onclick=()=>pwForm('Escolha a nova senha.',()=>{});
 box.querySelector('#b6o').onclick=async()=>{await sb.auth.signOut();try{Object.keys(window.localStorage).length}catch(e){}location.reload()}};
/* banco: mesmas operações que o app usava no Claude */
const TB={team:'team',pub:'pub'};
const row=(id,r)=>({id,exists:!!r,data:()=>r?{j:r.j,u:r.u,by:r.by}:undefined});
function coll(path){const t=TB[path];return{
 get:async()=>{if(!t)return{docs:[]};let all=[],f=0;for(;;){const {data,error}=await sb.from(t).select('id,j,u,by').order('id').range(f,f+999);if(error)throw error;all=all.concat(data);if(data.length<1000)break;f+=1000}return{docs:all.map(r=>row(r.id,r))}},
 doc:id=>({get:async()=>{if(!t)return row(id,null);const {data,error}=await sb.from(t).select('id,j,u,by').eq('id',id).maybeSingle();if(error)throw error;return row(id,data)},
  set:async v=>{if(!t)return;const {error}=await sb.from(t).upsert({id,j:v.j,u:v.u||Date.now(),by:v.by||''});if(error)throw error},
  delete:async()=>{if(!t)return;const {error}=await sb.from(t).delete().eq('id',id);if(error)throw error}})}}
const db={collection:coll,doc:p=>{const i=p.lastIndexOf('/');return coll(p.slice(0,i)).doc(p.slice(i+1))}};
const user={isOwner:async()=>true,canEdit:async()=>true,id:async()=>{const {data:{session}}=await sb.auth.getSession();return session?session.user.id:''},
 profiles:async ids=>{const {data}=await sb.from('admins').select('user_id,nome,email').in('user_id',ids||[]);const o={};(data||[]).forEach(a=>o[a.user_id]={name:a.nome||a.email});return o}};
/* arquivos (áudios, PDFs, imagens) no Storage do Supabase */
const ext=t=>({'audio/mpeg':'mp3','audio/mp4':'m4a','audio/x-m4a':'m4a','audio/wav':'wav','audio/x-wav':'wav','video/mp4':'mp4','application/pdf':'pdf','image/jpeg':'jpg','image/png':'png','image/webp':'webp'}[t]||'bin');
const assets={upload:async(b,o)=>{const ty=(o&&o.type)||b.type||'application/octet-stream',id=(crypto.randomUUID?crypto.randomUUID().replace(/-/g,''):Date.now().toString(36)+Math.random().toString(36).slice(2))+'.'+ext(ty);
  const {error}=await sb.storage.from(BUCKET).upload(id,b,{contentType:ty,upsert:false,cacheControl:'31536000'});if(error)throw error;
  return{id,url:sb.storage.from(BUCKET).getPublicUrl(id).data.publicUrl,sizeBytes:b.size}},
 delete:async id=>{const {error}=await sb.storage.from(BUCKET).remove([String(id)]);if(error)throw error}};
window.claude={use:async n=>{await ready;return n=='db'?db:n=='user'?user:n=='assets'?assets:null}};
const go=()=>check().catch(e=>loginForm('Sem conexão com o servidor. Tente de novo.'));
if(document.body)go();else document.addEventListener('DOMContentLoaded',go);
})();
