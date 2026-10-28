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
#b6l .ok{color:#7CCEDB;font-size:.88rem}#b6l .bd{width:44px;height:44px;border-radius:50%;border:2px solid #fff;display:grid;place-items:center;font-weight:800}`;
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
  if(a!==b){er.textContent='As senhas não conferem.';return}er.textContent='Salvando…';const {error}=await sb.auth.updateUser({password:a,data:{pw_ok:true}});
  if(error){er.textContent=pwErr(error);return}hide();if(after)after();else check();try{toast('Senha alterada')}catch(x){}}}

const pwErr=e=>/same|different/i.test(e.message||'')?'A nova senha precisa ser diferente da atual.':/weak|short|least|characters/i.test(e.message||'')?'Senha fraca: use pelo menos 8 caracteres, misturando letras e números.':'Não foi possível salvar: '+e.message;
function pwFirst(session){const nm=((session.user.email||'').split('@')[0]||'').replace(/</g,'');
 ui(`<form id="b6f">${head}<p><b style="color:#fff">Bem-vindo(a)!</b> Este é o seu primeiro acesso. Para proteger a conta, crie agora uma senha só sua, diferente da que você recebeu.</p><input id="b6p" type="password" autocomplete="new-password" placeholder="Nova senha (mín. 8 caracteres)" minlength="8" required><input id="b6q" type="password" autocomplete="new-password" placeholder="Repita a nova senha" minlength="8" required><p style="font-size:.78rem">Dica: use uma frase curta que só você saiba, com letras e números.</p><div class="er"></div><button type="submit">Salvar e entrar</button><button type="button" class="l" id="b6o">Sair</button></form>`);
 box.querySelector('#b6o').onclick=async()=>{try{localStorage.removeItem(OK)}catch(e){}await sb.auth.signOut();loginForm()};
 box.querySelector('#b6f').onsubmit=async e=>{e.preventDefault();const a=box.querySelector('#b6p').value,b=box.querySelector('#b6q').value,er=box.querySelector('.er');
  if(a.length<8){er.textContent='Use pelo menos 8 caracteres.';return}if(a!==b){er.textContent='As senhas não conferem.';return}
  er.className='er';er.textContent='Salvando…';const {error}=await sb.auth.updateUser({password:a,data:{pw_ok:true}});
  if(error){er.textContent=pwErr(error);return}try{localStorage.setItem(OK,session.user.id)}catch(x){}hide();okRes(session);setTimeout(()=>{try{toast('Senha criada. Bem-vindo(a)!')}catch(x){}},800)}}
async function mfaForm(msg){const {data}=await sb.auth.mfa.listFactors();const f=data&&data.totp&&data.totp.find(x=>x.status==='verified');if(!f){check();return}
 ui(`<form id="b6f">${head}<p>Digite o código de 6 dígitos do seu aplicativo autenticador.</p><input id="b6c" inputmode="numeric" autocomplete="one-time-code" maxlength="6" placeholder="000000" required><div class="er">${msg||''}</div><button type="submit">Confirmar</button><button type="button" class="l" id="b6o">Sair</button></form>`);
 box.querySelector('#b6o').onclick=async()=>{await sb.auth.signOut();loginForm()};
 box.querySelector('#b6f').onsubmit=async e=>{e.preventDefault();const er=box.querySelector('.er');er.textContent='Verificando…';
  const {error}=await sb.auth.mfa.challengeAndVerify({factorId:f.id,code:box.querySelector('#b6c').value.trim()});
  if(error){er.textContent='Código inválido. Confira o horário do celular e tente de novo.';return}check()}}
async function mfaOn(){const old=(await sb.auth.mfa.listFactors()).data;for(const x of (old&&old.all||[]).filter(x=>x.status!=='verified'))try{await sb.auth.mfa.unenroll({factorId:x.id})}catch(e){}
 const {data,error}=await sb.auth.mfa.enroll({factorType:'totp',friendlyName:'Escala B6 '+new Date().toISOString().slice(0,16)});
 if(error){ui(`<form>${head}<div class="er">Não foi possível ativar: ${error.message}</div><button type="button" id="b6v">Voltar</button></form>`);box.querySelector('#b6v').onclick=()=>window.b6Conta();return}
 ui(`<form id="b6f">${head}<p>1. Instale um app autenticador (Google Authenticator, Microsoft Authenticator ou similar).<br>2. Leia o QR code abaixo com ele.<br>3. Digite o código de 6 dígitos que aparecer.</p><img src="${data.totp.qr_code}" alt="QR code" style="width:180px;height:180px;background:#fff;border-radius:12px;padding:8px;align-self:center"><p style="font-size:.78rem;word-break:break-all">Sem câmera? Use esta chave: <b style="color:#fff">${data.totp.secret}</b></p><input id="b6c" inputmode="numeric" autocomplete="one-time-code" maxlength="6" placeholder="000000" required><div class="er"></div><button type="submit">Ativar</button><button type="button" class="l" id="b6v">Cancelar</button></form>`);
 box.querySelector('#b6v').onclick=async()=>{try{await sb.auth.mfa.unenroll({factorId:data.id})}catch(e){}window.b6Conta()};
 box.querySelector('#b6f').onsubmit=async e=>{e.preventDefault();const er=box.querySelector('.er');er.textContent='Verificando…';
  const {error}=await sb.auth.mfa.challengeAndVerify({factorId:data.id,code:box.querySelector('#b6c').value.trim()});
  if(error){er.textContent='Código inválido. Tente de novo.';return}hide();try{toast('Verificação em duas etapas ativada')}catch(x){}}}
async function mfaOff(){const {data}=await sb.auth.mfa.listFactors();for(const x of (data&&data.all)||[]){const {error}=await sb.auth.mfa.unenroll({factorId:x.id});if(error){ui(`<form>${head}<div class="er">Não foi possível desativar: ${error.message}</div><button type="button" id="b6v">Voltar</button></form>`);box.querySelector('#b6v').onclick=()=>window.b6Conta();return}}hide();try{toast('Verificação em duas etapas desativada')}catch(x){}}
let recovering=false;
sb.auth.onAuthStateChange((ev)=>{if(ev==='PASSWORD_RECOVERY'){recovering=true;pwForm('Crie a sua nova senha.')}});
const OK='b6adm';
function offSess(){try{const r=JSON.parse(localStorage.getItem('b6-auth')||'null');const u=r&&(r.user||(r.currentSession&&r.currentSession.user));return u&&localStorage.getItem(OK)===u.id?u:null}catch(e){return null}}
async function check(){if(recovering)return;
 if(!navigator.onLine){const u=offSess();if(u){hide();okRes({user:u});try{setTimeout(()=>setSt('Offline'),1500)}catch(e){}return}}
 let session=null;try{const r=await sb.auth.getSession();session=r.data.session}catch(e){}
 if(!session){const u=offSess();if(u&&!navigator.onLine){hide();okRes({user:u});return}loginForm();return}
 try{const a=await sb.auth.mfa.getAuthenticatorAssuranceLevel();if(a.data&&a.data.nextLevel==='aal2'&&a.data.currentLevel!=='aal2'){mfaForm();return}}catch(e){}
 let adm=null;try{const {data,error}=await sb.rpc('is_admin');if(error)throw error;adm=data===true}catch(e){if(localStorage.getItem(OK)===session.user.id){hide();okRes(session);return}loginForm('Sem conexão com o servidor. Tente de novo.');return}
 if(!adm){try{localStorage.removeItem(OK)}catch(e){}await sb.auth.signOut();loginForm('Esta conta não tem acesso de administrador.');return}
 if(!(session.user.user_metadata||{}).pw_ok){pwFirst(session);return}
 try{localStorage.setItem(OK,session.user.id)}catch(e){}hide();okRes(session)}
window.b6Conta=async()=>{const {data:{session}}=await sb.auth.getSession();const em=session&&session.user.email||'';let mf=false;try{const r=await sb.auth.mfa.listFactors();mf=!!(r.data&&r.data.totp&&r.data.totp.some(x=>x.status==='verified'))}catch(e){}
 try{dlg.close()}catch(e){}
 ui(`<form>${head}<p>Conectado como <b style="color:#fff">${em.replace(/</g,'')}</b></p><button type="button" id="b6s">Trocar senha</button><button type="button" class="l" id="b6m">${mf?'Desativar verificação em duas etapas':'Ativar verificação em duas etapas'}</button><button type="button" class="l" id="b6o" style="color:#ff8a8a">Sair deste aparelho</button><button type="button" class="l" id="b6v">Voltar ao app</button></form>`);
 box.querySelector('#b6m').onclick=()=>mf?mfaOff():mfaOn();box.querySelector('#b6v').onclick=hide;box.querySelector('#b6s').onclick=()=>pwForm('Escolha a nova senha.',()=>{});
 box.querySelector('#b6o').onclick=async()=>{try{localStorage.removeItem(OK)}catch(e){}await sb.auth.signOut();try{Object.keys(window.localStorage).length}catch(e){}location.reload()}};
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
 profiles:async ids=>{const {data}=await sb.from('admins').select('user_id,nome,email').in('user_id',ids||[]);const o={u_Nx1LSv4OSbBHt9e0NPxSOA:{name:'Thiago Galvão'}};(data||[]).forEach(a=>o[a.user_id]={name:a.nome||a.email});return o}};
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
