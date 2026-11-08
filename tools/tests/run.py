# Testes automáticos do Fervor (rodam no GitHub a cada atualização e podem rodar no computador).
# Uso: python3 tools/tests/run.py   (precisa de: pip install playwright && python -m playwright install chromium)
# Tudo é simulado: nenhum dado real é alterado e nenhuma chamada sai para o Supabase, Cifra Club ou YouTube.
import json, os, re, sys, subprocess, threading, functools, http.server, tempfile
from playwright.sync_api import sync_playwright

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
HERE = os.path.dirname(os.path.abspath(__file__))
FAIL = []
def ok(cond, name, info=''):
    print(('✔ ' if cond else '✘ ') + name + (f' — {info}' if info and not cond else ''))
    if not cond: FAIL.append(name)

# 0) o app.html precisa ser exatamente a junção dos módulos de tools/src
r = subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'montar.py'), '--check'], capture_output=True, text=True)
ok(r.returncode == 0, 'módulos de tools/src conferem com tools/app.html', r.stdout[-200:])

# 0b) CSS: não deixa crescer a pilha de regras sobrepostas (limites = situação de hoje; só podem diminuir)
import glob, collections
_css = ''.join(open(f, encoding='utf-8').read() for f in sorted(glob.glob(os.path.join(ROOT, 'tools', 'src', '0[0-4]_*.html'))))
_css = re.sub(r'/\*.*?\*/', '', _css, flags=re.S)
_imp = _css.count('!important')
_sel = collections.Counter(x.strip() for x, _ in re.findall(r'(?m)^([^{}@\n][^{}\n]*)\{([^{}]*)\}', _css))
_dup = sum(1 for k, n in _sel.items() if n > 1)
ok(_imp <= 251, f'CSS: no máximo 251 usos de !important (hoje {_imp})')
ok(_dup <= 43, f'CSS: no máximo 43 seletores repetidos (hoje {_dup})')

# 0c) compatibilidade com Safari 15 (iPad Air 2 / iOS 15): nada de lookbehind em regex nem de bloco "static {}" (derrubam o app inteiro)
_js = open(os.path.join(ROOT, 'tools', 'app.html'), encoding='utf-8').read()
_ruim = re.findall(r'\(\?<[=!]|static\s*\{|\.findLast\(|\.toSorted\(|\.toReversed\(|structuredClone\(|Object\.groupBy|AbortSignal\.timeout|Promise\.withResolvers|Array\.fromAsync|[\w\)\]]\.at\(-?\d', _js)
ok(not _ruim, 'compatível com Safari 15 (iPad antigo): sem recursos novos demais', str(sorted(set(_ruim))[:5]))

# 1) sintaxe do JavaScript das páginas
for f in ['index.html', 'admin/index.html']:
    s = open(os.path.join(ROOT, f), encoding='utf-8').read()
    for i, sc in enumerate(re.findall(r'<script>([\s\S]*?)</script>', s)):
        t = tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8'); t.write(sc); t.close()
        r = subprocess.run(['node', '--check', t.name], capture_output=True, text=True); os.unlink(t.name)
        ok(r.returncode == 0, f'sintaxe {f} bloco {i+1}', r.stderr[-300:])
for f in ['app.js', 'admin/app.js', 'sw.js', 'tools/shim.js', 'tools/sbshim.js']:
    p = os.path.join(ROOT, f)
    if os.path.exists(p):
        r = subprocess.run(['node', '--check', p], capture_output=True, text=True); ok(r.returncode == 0, f'sintaxe {f}', r.stderr[-300:])

class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=ROOT))
PORT = srv.server_address[1]; threading.Thread(target=srv.serve_forever, daemon=True).start()
B = f'http://127.0.0.1:{PORT}'

PUB = json.load(open(os.path.join(ROOT, 'pub.json'), encoding='utf-8'))
import unicodedata
def _nz(x): return ''.join(c for c in unicodedata.normalize('NFD', str(x or '').lower()) if unicodedata.category(c) != 'Mn').strip()
_G = set()
for _k, _v in PUB.items():
    if _k.startswith('l_'):
        _j = json.loads(_v['j']); _G.add((_j.get('date'), _nz(_j.get('place')), _nz(_j.get('turno')), _nz(_j.get('name'))) if _j.get('date') else _k)
NL = len(_G)  # cultos duplicados (mesmo dia/local/horário) aparecem como um só
STUB = open(os.path.join(HERE, 'stub.js'), encoding='utf-8').read()
CC = open(os.path.join(HERE, 'cifra_exemplo.html'), encoding='utf-8').read()
SOLR = {'response': {'docs': [{'txt': 'Canção de Teste', 'art': 'Grupo Exemplo', 'dns': 'grupo-exemplo', 'url': 'cancao-de-teste', 'imgm': ''}]}}
XSS = '"><img src=x onerror="window.__x=1"><svg onload=window.__x=2>'

def ctx_of(b, w=390, h=844):
    c = b.new_context(viewport={'width': w, 'height': h}, service_workers='block')
    c.route('**/fonts.googleapis.com/**', lambda r: r.abort()); c.route('**/i.ytimg.com/**', lambda r: r.abort())
    c.route('https://r.jina.ai/**', lambda r: r.fulfill(status=200, content_type='text/plain' if r.request.url.endswith('imprimir.html') else 'text/html', body='[Ritmo] 72 bpm' if r.request.url.endswith('imprimir.html') else CC, headers={'access-control-allow-origin': '*'}))
    c.route('https://solr.sscdn.co/**', lambda r: r.fulfill(status=200, content_type='application/json', body=json.dumps(SOLR), headers={'access-control-allow-origin': '*'}))
    c.route('https://www.youtube.com/oembed**', lambda r: r.fulfill(status=200, content_type='application/json', body=json.dumps({'title': 'Grupo Exemplo - Canção de Teste (Ao Vivo)', 'author_name': 'Grupo Exemplo'}), headers={'access-control-allow-origin': '*'}))
    return c

with sync_playwright() as p:
    b = p.chromium.launch()
    # 2) visão da banda (dados de pub.json, sem login)
    c = ctx_of(b); c.route('**/*.supabase.co/**', lambda r: r.fulfill(status=200, content_type='application/json', body='[]'))
    c.add_init_script("try{localStorage.setItem('rep.tour','1');localStorage.setItem('rep.meask','1')}catch(e){}")
    pg = c.new_page(); E = []; pg.on('pageerror', lambda x: E.append(str(x)[:200]))
    pg.goto(B + '/'); pg.wait_for_timeout(3500)
    n = pg.evaluate('S.lists.length'); ok(n == NL, 'banda: todos os cultos publicados aparecem', f'{n} de {NL}')
    inc = pg.evaluate("S.lists.filter(l=>l.songIds.some(id=>!S.songs.find(s=>s.id==id))).length"); ok(inc == 0, 'banda: nenhum culto com música faltando', f'{inc} cultos incompletos')
    lid = pg.evaluate("(S.lists.filter(l=>l.songIds.length&&l.date).sort((a,b)=>b.date.localeCompare(a.date))[0]||{}).id")
    if lid:
        pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d=>d.close())")
        pg.evaluate(f"S.tab='lists';S.lv='{lid}';S.lvm=1;R()"); pg.wait_for_timeout(300)
        ok(pg.evaluate(f"document.querySelectorAll('#lvl li[data-id]').length") > 0, 'banda: repertório mostra as músicas')
        pg.evaluate("document.querySelector('#lvl li[data-id] .it.sc').click()"); pg.wait_for_timeout(400)
        ok(pg.evaluate("S.tab=='songs'&&!!S.sel"), 'banda: abre a música do repertório')
        pg.evaluate(f"stage('{lid}')"); pg.wait_for_timeout(300); i0 = pg.evaluate(f"S.lists.find(l=>l.id=='{lid}').songIds.indexOf(S.sel)")
        pg.keyboard.press('ArrowRight'); pg.wait_for_timeout(200); i1 = pg.evaluate(f"S.lists.find(l=>l.id=='{lid}').songIds.indexOf(S.sel)")
        ok(i1 - i0 == 1, 'banda: seta do teclado no Modo Palco passa uma música', f'{i0}->{i1}'); pg.evaluate('fsExit()')
        # 2b) player de Stems: abre e fecha com Esc sem vazar AudioContext/áudio
        sid0 = pg.evaluate("S.songs.find(s=>s.id==S.sel)?S.sel:S.songs[0].id")
        pg.evaluate(f"(()=>{{const s=S.songs.find(x=>x.id=='{sid0}');s.stems={{vocal:'./naoexiste-vocal.wav',bateria:'./naoexiste-bateria.wav',em:Date.now()}};fxmOpen('{sid0}')}})()")
        pg.wait_for_timeout(400)
        ok(pg.evaluate("d2.open===true&&FXA.length===2"), 'stems: abre o player com as faixas disponíveis')
        pg.wait_for_timeout(600)
        ok(pg.evaluate("$('#fxload').style.display==='block'&&$('#fxload').textContent.includes('Não consegui carregar')"), 'stems: avisa quando nenhuma faixa consegue carregar (em vez de falhar calado)')
        ok(pg.evaluate("$('#fxpp').disabled===true"), 'stems: desabilita o play quando todas as faixas falham')
        pg.keyboard.press('Escape'); pg.wait_for_timeout(300)
        ok(pg.evaluate("d2.open===false&&FXA.length===0&&!FXCTX"), 'stems: fechar com Esc libera o áudio (sem vazamento)')
    r = pg.evaluate("""()=>{document.querySelectorAll('dialog[open]').forEach(d=>d.close());tab('songs');S.hide=false;R();
      const q=document.getElementById('q'),cs=getComputedStyle(q).display,btn=[...document.querySelectorAll('#tbb [data-t="songs"]')].some(e=>getComputedStyle(e).display!='none'),
      qb=getComputedStyle(document.getElementById('qb')).display,add=getComputedStyle(document.getElementById('add')).display,items=document.querySelectorAll('#ls .it').length,mais=document.querySelector('.lt [title="Mais opções"]');
      const hm=mais&&mais.hidden;pick(S.songs[0].id);const ed=[...document.querySelectorAll('[onclick^="editSong"],[onclick^="delSong"]')].filter(e=>getComputedStyle(e).display!='none').length;const detail=!!document.querySelector('.hd');
      S.tab='lists';S.hide=false;R();return{cs,qb,btn,add,items,hm,ed,detail}}""")
    ok(r['qb'] != 'none' and r['btn'] and r['add'] == 'none' and r['items'] > 10 and r['hm'] and r['ed'] == 0 and r['detail'], 'banda: menu Músicas lista e abre qualquer música, sem opções de edição', str(r))
    r = pg.evaluate("""()=>{const T=td(),l=S.lists.filter(x=>x.date&&x.date>=T).sort((a,b)=>a.date.localeCompare(b.date))[0];const o=[l.banda,ME_M,MY_DISP,window.__SBB,localStorage.getItem('rep.me')];l.banda={...(l.banda||{}),vm:'Ana Teste'};ME_M={id:'m1',nome:'Ana Teste'};MY_DISP={};window.__SBB={};try{localStorage.setItem('rep.me','Ana Teste')}catch(e){}
     S.tab='hoje';R();const a=[],cf=()=>document.querySelector('.hjcf'),mo=()=>document.querySelector('.hjmo');
     a.push(!!cf(),!mo());MY_DISP[l.id]={status:'sim'};R();a.push(!cf(),!!mo(),/Presença confirmada/.test(document.querySelector('.hjhero').textContent));hjMais(l.id);a.push(d2.open&&d2.dataset.k=='sheet'&&/Vou servir/.test(d2.textContent));d2.close();
     [l.banda,ME_M,MY_DISP,window.__SBB]=o.slice(0,4);if(o[4]==null)localStorage.removeItem('rep.me');else localStorage.setItem('rep.me',o[4]);S.tab='lists';R();return a}""")
    ok(r == [True, True, True, True, True, True], 'banda: Confirmar presença no Hoje até confirmar; depois fica em Mais', str(r))
    r = pg.evaluate("""async()=>{const T=td(),l=S.lists.filter(x=>x.date&&x.date>=T).sort((a,b)=>a.date.localeCompare(b.date))[0];const o=[l.banda,ME_M,MY_DISP,window.__SBB,window.__FVME,localStorage.getItem('rep.me')];l.banda={...(l.banda||{}),vm:pubNm('Ana Teste')};ME_M=null;MY_DISP={};try{localStorage.removeItem('rep.me')}catch(e){}
     const q={select:()=>q,eq:()=>q,then:f=>f({data:[]})};window.__SBB={auth:{getUser:async()=>({data:{user:{id:'u',email:'a@b.c'}}})},from:()=>q};window.__FVME={id:'m1',nome:'Ana Teste'};
     S.tab='hoje';R();const a=[!document.querySelector('.hjcf')];await fvInit();a.push(!!document.querySelector('.hjcf'));
     [l.banda,ME_M,MY_DISP,window.__SBB,window.__FVME]=o.slice(0,5);if(o[5]==null)localStorage.removeItem('rep.me');else localStorage.setItem('rep.me',o[5]);S.tab='lists';R();return a}""")
    ok(r == [True, True], 'banda: ao entrar na conta, o Confirmar presença aparece no Hoje sem precisar sair da tela', str(r))
    r = pg.evaluate("""()=>{const o=[ME_M,window.__SBB];ME_M={id:'m1',nome:'Ana Teste'};window.__SBB={};S.tab='hoje';R();const a=[!!document.querySelector('.hjcol > .hjbar'),!document.querySelector('.hjhero .hjb')];S.tab='perf';R();const d=document.querySelector('details.dmo2');a.push(!!d&&!d.open,!!d&&/Mais/.test(d.textContent));[ME_M,window.__SBB]=o;S.tab='lists';R();return a}""")
    ok(r == [True, True, True, True], 'um jeito só: barra de ações do Hoje fora do cartão e disponibilidade do Perfil em "Mais"', str(r))
    r = pg.evaluate("""async()=>{const a=[],u='https://thiagorgalvao-sketch.github.io/escala-b6/media/46b9579c1e83de4b8b69c1b9d6cc915b.mp3';
     a.push(locU(u)==location.origin+'/media/46b9579c1e83de4b8b69c1b9d6cc915b.mp3',locU('https://x.supabase.co/storage/v1/object/public/midias/a.mp4')=='https://x.supabase.co/storage/v1/object/public/midias/a.mp4');
     const b=await getBl(u);a.push(b.size>100000);return a}""")
    ok(r == [True, True, True], 'baixar para offline: áudios do site são buscados no mesmo endereço do app (sem bloqueio entre domínios)', str(r))
    r = pg.evaluate("""()=>{const a=[];const l=S.lists.find(x=>x.banda&&Object.values(x.banda).some(Boolean));const kk=Object.keys(l.banda).find(k=>l.banda[k]),antes=l.banda[kk],nome='Fulano Lembrete Teste';l.banda[kk]=nome;const d0=l.date,z=n=>String(n).padStart(2,'0'),mais=k=>{const x=new Date(td()+'T12:00');x.setDate(x.getDate()+k);return x.getFullYear()+'-'+z(x.getMonth()+1)+'-'+z(x.getDate())};
     l.date=mais(1);try{localStorage.setItem('rep.me',nome);localStorage.removeItem('rep.lemb');localStorage.removeItem('rep.cf')}catch(e){}
     a.push(!!lembAlvo());const f=lembPres();a.push(f&&/Amanhã é culto/.test(document.querySelector('#tt').textContent));a.push(lembPres()===false);
     cfS(l.id,'s');a.push(lembAlvo()===null);localStorage.removeItem('rep.cf');localStorage.removeItem('rep.lemb');l.date=mais(10);a.push(lembAlvo()===null);l.date=d0;l.banda[kk]=antes;localStorage.removeItem('rep.me');return a}""")
    ok(r == [True]*5, 'lembrete de presença: avisa 1 vez por dia, some ao responder e só para culto de hoje/amanhã', str(r))
    ok(not E, 'banda: sem erros de JavaScript', '; '.join(E[:3])); c.close()

    # 2b) Hoje abre na hora pela cópia salva e atualiza por trás sem mexer na tela
    SGc = [json.loads(v['j']) for k, v in PUB.items() if k.startswith('s_')]; LSc = [json.loads(v['j']) for k, v in PUB.items() if k.startswith('l_')]
    c = ctx_of(b); held = []
    c.route('**/*.supabase.co/**', lambda r: held.append(r)); c.route('**/pub.json**', lambda r: held.append(r))
    c.add_init_script("try{localStorage.setItem('rep.tour','1');localStorage.setItem('rep.meask','1');localStorage.setItem('rep.role','band');localStorage.setItem('rep.band',%s)}catch(e){}" % json.dumps(json.dumps({'SG': SGc, 'LS': LSc, 'E': None, 't': 1})))
    pg2 = c.new_page(); E2 = []; pg2.on('pageerror', lambda x: E2.append(str(x)[:200]))
    pg2.goto(B + '/'); pg2.wait_for_timeout(1200)
    r = pg2.evaluate("({tab:S.tab,n:S.lists.length,hoje:!!document.querySelector('.hjhero'),off:S.bOff,held:0})")
    ok(r['tab'] == 'hoje' and r['n'] > 0 and r['hoje'] and not r['off'] and len(held) > 0, 'Hoje abre na hora com a cópia salva (sem esperar a internet)', str(r) + ' pendentes=' + str(len(held)))
    pg2.evaluate("S.tab='lists';S.lvm=0;R()")
    for rt in list(held):
        try:
            if 'pub.json' in rt.request.url: rt.fulfill(status=200, content_type='application/json', path=os.path.join(ROOT, 'pub.json'))
            else: rt.fulfill(status=200, content_type='application/json', body='[]')
        except Exception: pass
    pg2.wait_for_timeout(2500)
    r = pg2.evaluate("({tab:S.tab,n:S.lists.length,off:S.bOff})")
    ok(r['tab'] == 'lists' and r['n'] > 0 and not E2, 'atualização pela internet não tira o usuário da tela em que está', str(r) + str(E2))
    for rt in list(held):
        try: rt.abort()
        except Exception: pass
    try: pg2.close()
    except Exception: pass
    c.close()
    # 3) painel dos administradores (Supabase simulado)
    lists = [{'id': k, 'j': v['j']} for k, v in PUB.items()]
    DB = {'users': [{'id': 'u1', 'email': 'adm@teste.local', 'password': 'senha123', 'meta': {'pw_ok': True}}], 'admins': [{'user_id': 'u1', 'email': 'adm@teste.local'}],
          'membros': [], 'config': [], 'disponibilidade': [], 'team': [dict(x, u=1) for x in lists], 'pub': lists}
    c = ctx_of(b)
    c.route('**/vendor/supabase.min.js', lambda r: r.fulfill(status=200, content_type='application/javascript', body=STUB))
    c.route('**/cdn.jsdelivr.net/**supabase**', lambda r: r.fulfill(status=200, content_type='application/javascript', body=STUB))
    c.route('**/*.supabase.co/**', lambda r: r.fulfill(status=200, content_type='application/json', body='[]'))
    c.add_init_script("if(!localStorage.getItem('__seeded')){localStorage.setItem('__seeded','1');localStorage.setItem('__stubdb',%s);localStorage.setItem('adm:rep.tour','1')}" % json.dumps(json.dumps(DB)))
    pg = c.new_page(); E = []; pg.on('pageerror', lambda x: E.append(str(x)[:200]))
    pg.goto(B + '/admin/'); pg.wait_for_timeout(1500)
    pg.fill('#b6e', 'adm@teste.local'); pg.fill('#b6p', 'senha123'); pg.click('#b6f button[type=submit]'); pg.wait_for_timeout(6000)
    ok(pg.evaluate('!!window.__SYNCOK'), 'admin: login e sincronização')
    # 3b) publicar culto futuro: a visão da banda recebe as músicas
    r = pg.evaluate("""async()=>{const l=S.lists.filter(x=>x.songIds.length&&x.date).sort((p,q)=>p.date.localeCompare(q.date))[0];l.date='2099-01-01';delete l.pub;const id=l.id;
     save();await pubSync();const d=await claude.use('db');const q=await d.collection('pub').get();const x=q.docs.find(y=>y.id=='l_'+id);const o=JSON.parse(x.data().j);
     return{n:o.songIds.length,esp:l.songIds.length,pub:true}}""")
    ok(r['n'] == r['esp'] and r['pub'], 'admin: salvar culto futuro já envia as músicas para a banda (sem publicar)', str(r))
    r = pg.evaluate("""async()=>{await pubSync();const q=await(await claude.use('db')).collection('pub').get();const ids=new Set(q.docs.map(y=>y.id));return[q.docs.filter(y=>y.id[0]=='s').length,new Set(S.songs.map(s=>s.id)).size,S.songs.filter(s=>!ids.has('s_'+s.id)).map(s=>s.id+':'+s.title).slice(0,3),JSON.stringify((window.__PUBST||{}).err)]}""")
    ok(r[0] == r[1] and r[1] > 0, 'admin: todas as músicas vão para a visão da banda (para buscar na hora)', str(r))
    pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d=>d.close())")
    n0 = pg.evaluate('S.songs.length')
    pg.evaluate("editSong()"); pg.fill('#nsq', 'cancao de teste'); pg.click('#dlg button:has-text("Buscar")'); pg.wait_for_timeout(800)
    pg.click('#nsr .cbi >> nth=0'); pg.wait_for_timeout(1200)
    d = pg.evaluate("({t:D.title,k:D.key,bpm:D.bpm,n:D.parts.filter(q=>q.chords).length,cc:D.cc})")
    ok(d['k'] == 'A' and d['n'] >= 2 and d['bpm'] == 72, 'admin: nova música pela busca traz cifra, tom, BPM e blocos', str(d))
    pg.evaluate("ssong()"); pg.wait_for_timeout(500); ok(pg.evaluate('S.songs.length') == n0 + 1, 'admin: salvar música nova')
    sid = pg.evaluate("S.songs[0].id"); pg.evaluate(f"editSong('{sid}')"); pg.fill('.etit', 'Alterado'); pg.click('#dlg button:has-text("Cancelar")'); pg.wait_for_timeout(200)
    ok(pg.evaluate("dlg.open&&d2.open"), 'admin: avisa antes de sair sem salvar'); pg.evaluate("d2.close();D0='';dlg.close()")
    # 4) disponibilidade da equipe: borda colorida + motivo da recusa, sem caixa duplicada
    lid2 = pg.evaluate("(S.lists.filter(l=>l.songIds.length&&l.date).sort((p,q)=>p.date.localeCompare(q.date))[0]||{}).id")
    if lid2:
        pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d=>d.close())")
        pg.evaluate("(id=>{const l=S.lists.find(x=>x.id==id);l.date='2099-01-01';l.banda=Object.assign({},l.banda,{vm:'Teste Confirma',bt:'Teste Recusa'});DISP_ALL={[id]:[{nome:'Teste Confirma',status:'sim',obs:''},{nome:'Teste Recusa',status:'nao',obs:'Motivo X'}]};S.tab='lists';S.lv=id;S.lvm=1;R()})(%r)" % lid2)
        pg.wait_for_timeout(300)
        ok(pg.evaluate("document.querySelectorAll('.esp.dok').length") > 0, 'disponibilidade: confirmação mostra borda verde na equipe')
        ok(pg.evaluate("document.querySelectorAll('.esp.dno').length") > 0, 'disponibilidade: recusa mostra borda vermelha na equipe')
        ok(pg.evaluate("[...document.querySelectorAll('.espw')].some(e=>e.textContent.includes('Motivo X'))"), 'disponibilidade: motivo da recusa aparece junto ao nome')
        ok(pg.evaluate("document.querySelectorAll('.dpx').length") == 0, 'disponibilidade: sem caixa duplicada separada')
        pg.evaluate("DISP_ALL=null")
    # 5) backup e restauração: textarea reflete os dados e restaurar volta ao estado salvo
    pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d=>d.close())")
    n0s, n0l = pg.evaluate('S.songs.length'), pg.evaluate('S.lists.length')
    pg.evaluate('bk()'); pg.wait_for_timeout(200)
    ok(pg.evaluate("$('#bt').value.length") > 100, 'backup: gera o conteúdo com os dados atuais')
    pg.evaluate("S.songs.push({id:'fake-test-song',title:'FAKE',artist:'',medleys:[],key:'',parts:[]})")
    pg.evaluate('rs()'); pg.wait_for_timeout(200)
    pg.click('#y2'); pg.wait_for_timeout(300)
    ok(pg.evaluate('S.songs.length') == n0s and not pg.evaluate("S.songs.some(s=>s.id=='fake-test-song')"), 'backup: restaurar descarta mudanças feitas depois do backup')
    ok(pg.evaluate('S.lists.length') == n0l, 'backup: restaurar preserva a contagem de repertórios')
    pg.evaluate("dlg.close()")
    # 5b) stems por áudio: Original, VS e Banda
    pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d=>d.close())")
    r = pg.evaluate("""()=>{const u='https://hofrthndlstofytlapzk.supabase.co/storage/v1/object/public/midias/a.mp3',F={vocal:'https://x/v.mp3',bateria:'https://x/b.mp3',em:'2026-11-03'};
     const s={id:'t-stems',title:'T',artist:'',medleys:[],key:'',parts:[],stems:F,stemsSrc:{url:u,name:'o.mp3'},vs:{url:u,name:'vs.mp3',stems:F},bas:[{url:u+'?b',name:'b.mp3',date:'2026-10-01',stems:F}]};
     const a=stAll(s);return{n:a.length,ks:a.map(x=>x[0]).join(','),src:stSrc(s,'v'),lk:stSrc({vs:{url:'https://youtu.be/x'}},'v'),ck:stSrc({vs:{url:'ck:https://x'}},'v'),hk:bh(u+'?b')==a[2][0]}}""")
    ok(r['n'] == 3 and r['ks'].startswith('o,v,b') and r['hk'], 'stems: Original, VS e Banda aparecem como fontes separadas')
    ok(r['src'].startswith('https://') and r['lk'] == '' and r['ck'] == '', 'stems: só áudio enviado como arquivo pode ser separado (link e partes não)')
    pg.evaluate("(()=>{D={id:'t-stems2',title:'T2',artist:'',medleys:[],key:'',parts:[],vs:{url:'https://hofrthndlstofytlapzk.supabase.co/storage/v1/object/public/midias/v.mp3',name:'v.mp3'},bas:[]};S.songs.push(D);S.band=false;DT='midia';dlg.showModal();sfR()})()")
    pg.wait_for_timeout(300)
    ok(pg.evaluate("[...document.querySelectorAll('.ebad')].map(e=>e.textContent).join(',')").endswith('ORIGINAL,VS,BANDA'), 'stems: aba Áudios tem Original, VS e Banda')
    ok(pg.evaluate("sepAuto()") is True and pg.evaluate("!!document.querySelector('input[onchange*=sepAutoSet]:checked')"), 'stems: separação automática vem marcada por padrão')
    ok(pg.evaluate("!!document.querySelector('.vsb .earow .vsbt')"), 'stems: cada áudio enviado tem seu botão STEMS')
    pg.evaluate("dlg.close();S.songs=S.songs.filter(x=>x.id!='t-stems2');D=null")
    r = pg.evaluate("""()=>{const F={vocal:'https://x/v.mp3',em:'2026-11-03'},u='https://hofrthndlstofytlapzk.supabase.co/storage/v1/object/public/midias/a.mp3';
     const s={id:'t-bt',title:'T',artist:'',medleys:[],key:'',parts:[],link:'https://youtu.be/dQw4w9WgXcQ',stems:F,stemsSrc:{url:u,name:'o.mp3'}};S.songs.push(s);
     const h=qkB(s),a=lkSlot(s.link);S.songs=S.songs.filter(x=>x.id!='t-bt');
     return{st:/>STEMS</.test(h),or:/>ORIGINAL</.test(h)&&/>VS</.test(h)&&/>BANDA</.test(h),yt:/lkGo[(]this[)]/.test(a),g:lkGo({getAttribute:()=>'https://youtu.be/dQw4w9WgXcQ'})===false&&!!document.querySelector('#ytp')}}""")
    ok(not r['st'] and r['or'], 'botões: ORIGINAL, VS e BANDA (sem botão STEMS separado)')
    ok(r['yt'] and r['g'], 'youtube: link abre o player dentro do app')
    r = pg.evaluate("""()=>{const a=[];const s=S.songs.find(x=>x.parts&&x.parts.length>2)||S.songs[0];S.tab='songs';S.sel=s.id;S.hide=true;S.vw='cifra';R();ytOpen('https://youtu.be/dQw4w9WgXcQ',s.id);
     const send=i=>window.dispatchEvent(new MessageEvent('message',{origin:'https://www.youtube-nocookie.com',data:JSON.stringify({event:'infoDelivery',info:i})}));
     a.push(typeof ytHi=='function',!YTP.got);send({playerState:1,duration:200,currentTime:100});a.push(!!YTP.got,YTP.state==1,/\\d+:\\d\\d \\/ 3:20/.test(document.querySelector('#ytst').textContent));ytClose();S.tab='lists';R();return a}""")
    ok(r == [True, True, True, True, True], 'youtube: o player responde ao app (aperto de mão correto) e passa a acompanhar a cifra', str(r))
    r = pg.evaluate("""()=>{const a=[];const s=S.songs.find(x=>x.parts&&x.parts.length>2)||S.songs[0];s.link='https://youtu.be/dQw4w9WgXcQ';S.tab='songs';S.sel=s.id;S.hide=true;S.vw='cifra';R();
     const b=document.querySelector('.asfx .pbm');a.push(!!b,!b.classList.contains('on'));ytOpen('https://youtu.be/dQw4w9WgXcQ',s.id);
     window.dispatchEvent(new MessageEvent('message',{origin:'https://www.youtube-nocookie.com',data:JSON.stringify({event:'infoDelivery',info:{playerState:1,duration:200,currentTime:50}})}));
     a.push(document.querySelector('.pbm').classList.contains('on'),/0:50 \\/ 3:20/.test(document.querySelector('#pbl').textContent));ytClose();a.push(!document.querySelector('.pbm').classList.contains('on'));S.tab='lists';R();return a}""")
    ok(r == [True, True, True, True, True], 'barra única: play/pausa, tempo e rolagem seguem o vídeo', str(r))
    pg.evaluate("ytClose()")
    r = pg.evaluate("()=>{const k=CK;CK='C';const a=dgr('C Dm Em F G Am Bdim Am7 Eb');CK='Am';const b=dgr('Am Dm Em C');CK=k;return[a,b]}")
    ok(r[0].startswith('1 2 3 4 5 6 7dim 6m7'), 'graus: grau naturalmente menor não leva "m" (6, não 6m)', str(r))
    ok(r[1] == '6 2 3 1', 'graus: tom menor também sem "m" nos graus naturais', str(r))
    # 5c) player de stems: minimizar mantém o áudio e mostra a barra; expandir volta; fechar para tudo
    r = pg.evaluate("""async()=>{const F={vocal:'https://x/v.mp3',bateria:'https://x/b.mp3',em:'2026-11-03'};
     const s={id:'t-fxm',title:'Teste FX',artist:'',medleys:[],key:'',parts:[],stems:F};S.songs.push(s);
     fxmOpen('t-fxm','o');const a=d2.open&&!!$('#fxpp')&&!!$('.fxmin')&&!!$('#fxseek');
     fxMin();const b=!d2.open&&!!$('#fxmini')&&FXMIN&&FXA.length==2;
     fxExpand();const c=d2.open&&!!$('#fxpp')&&!$('#fxmini')&&!FXMIN;
     fxMin();fxMiniClose();const d=!$('#fxmini')&&FXA.length==0&&!FXMIN;
     if(d2.open)d2.close();S.songs=S.songs.filter(x=>x.id!='t-fxm');return[a,b,c,d]}""")
    ok(r[0], 'player: tem minimizar, barra de tempo e controles')
    ok(r[1], 'player: minimizar fecha a janela, mantém as faixas e mostra a barra pequena')
    ok(r[2], 'player: expandir restaura o player completo')
    ok(r[3], 'player: fechar pela barra pequena para o áudio')
    r = pg.evaluate("()=>{const l={id:'t-pb',name:'X',songIds:[]};window.__PUBERR='';const a=pubBar(l);window.__PUBERR='falha X';const b=pubBar(l);window.__PUBERR='';return[a,/falha X/.test(b)]}")
    ok(r[0] == '' and r[1], 'admin: sem botão de publicar; aviso só quando a atualização do time falha')
    r = pg.evaluate("()=>{const a=lMerge([{id:'e_x',date:'2099-01-01',place:'Mauá',turno:'Manhã',songIds:[],banda:{bx:'Thiago',vm:''},passHora:'07:40'},{id:'r1',date:'2099-01-01',place:'Maua',turno:'Manhã',songIds:['a','b'],banda:{vm:'Josué',bx:''}}]);return a.length==1&&a[0].id=='r1'&&a[0].songIds.length==2&&a[0].banda.bx=='Thiago'&&a[0].banda.vm=='Josué'&&a[0].passHora=='07:40'}")
    ok(r, 'banda: cultos duplicados no mesmo dia/local/horário viram um só, com as músicas')
    r = pg.evaluate("()=>{const l={id:'t-pd',date:'2099-01-01',name:'X',songIds:[],banda:{}};const a=pendBox(l);return[/pendência/.test(a),/ltG\\('mu'\\)/.test(a),/ltG\\('ev'\\)/.test(a)]}")
    ok(all(r), 'admin: repertório mostra as pendências com atalho para resolver', str(r))
    r = pg.evaluate("()=>{const n0=S.lists.length;S.lists.push({id:'dupA',date:'2099-02-02',place:'Mauá',turno:'Noite',name:'Culto',songIds:[],banda:{bx:'Fulano'}},{id:'dupB',date:'2099-02-02',place:'Maua',turno:'Noite',name:'Culto',songIds:[S.songs[0].id],banda:{}});S.lv='dupA';const k=lDedup();const b=S.lists.find(l=>l.id=='dupB');return k==1&&S.lists.length==n0+1&&!S.lists.some(l=>l.id=='dupA')&&b.banda.bx=='Fulano'&&S.lv=='dupB'&&DQ.has('l_dupA')}")
    ok(r, 'admin: culto duplicado é unido ao que tem músicas (card do próximo culto = culto cadastrado)')
    pg.evaluate("S.lists=S.lists.filter(l=>l.id!='dupB');S.lv=null")
    r = pg.evaluate("()=>{const a=lMerge([{id:'e_y',date:'2099-03-03',place:'A',turno:'M',name:'C',songIds:[],apv:{st:'env',t:1000,by:'manu'}},{id:'r_y',date:'2099-03-03',place:'A',turno:'M',name:'C',songIds:['x'],apv:{st:'env',t:5000,by:'tg'}}]);return a.length==1&&a[0].apv.by=='manu'}")
    ok(r, 'admin: ao unir cultos, mantém o envio original à liderança (quem enviou primeiro)')
    r = pg.evaluate("""async()=>{let f=0;const of=window.fetch;window.fetch=(...a)=>{f++;return of(...a)};const u='https://hofrthndlstofytlapzk.supabase.co/storage/v1/object/public/midias/teste-grande.mp3';const t0=Date.now();const x=await msrc(u,1);window.fetch=of;return{same:x===u,f,ms:Date.now()-t0}}""")
    ok(r['same'] and r['f'] == 0, 'áudio: toca direto do link, sem baixar o arquivo inteiro antes (celular)', str(r))
    r = pg.evaluate("()=>{S.tab='hoje';R();const h=document.querySelector('.hj');const l=S.lists.find(x=>x.songIds.length);const s=S.songs.find(x=>x.id==l.songIds[0]);sgMenu(s.id,l.id);const n=document.querySelectorAll('#dlg2 .mni').length;d2.close();S.tab='lists';R();return[!!h,n]}")
    ok(r[0] and r[1] == 6, 'tela Hoje e menu de opções da música (jeito Apple)', str(r))
    r = pg.evaluate("""()=>{const u='https://hofrthndlstofytlapzk.supabase.co/storage/v1/object/public/midias/a.mp3',F={vocal:'x'};const l={id:'L',date:'2099-01-01'};
     const T=s=>(sgSrc(s,l)||{}).t;return[T({id:'a',stems:F,vs:{url:u,stems:F},bas:[{url:u,stems:F}]}),T({id:'b',vs:{url:u,stems:F},bas:[{url:u,stems:F}],stemsSrc:{url:u}}),T({id:'c',bas:[{url:u,stems:F}],stemsSrc:{url:u}}),T({id:'d',stemsSrc:{url:u},vs:{url:u},bas:[{url:u}]}),T({id:'e',vs:{url:u},bas:[{url:u}]}),T({id:'f',bas:[{url:u}],link:'https://youtu.be/dQw4w9WgXcQ'}),T({id:'g',link:'https://youtu.be/dQw4w9WgXcQ'})]}""")
    ok(r == ['Stems do original','Stems do VS','Stems da banda','Versão original','VS','Gravação da banda','YouTube'], 'play: prioridade stems original > stems VS > stems banda > original > VS > banda > YouTube', str(r))
    r = pg.evaluate("()=>{S.tab='hoje';R();const b=[...document.querySelectorAll('.hjb button')].find(x=>/Repert/.test(x.textContent));if(!b)return 'sem botão';b.click();return S.tab=='lists'&&S.lvm==1}")
    ok(r is True, 'Hoje: botão Repertório abre o culto', str(r))
    r = pg.evaluate("""async()=>{const nx=nextL();if(nx&&!nx.songIds.length)nx.songIds=S.songs.slice(0,2).map(x=>x.id);tourStart(1);const seen=[];for(let i=0;i<20&&$('#tour');i++){await new Promise(r=>setTimeout(r,120));const b=$('#tour .tcd b');seen.push(b?b.textContent:'');tourGo(1)}return seen}""")
    ok(len(r) >= 6 and 'Hoje' in r and 'Tocar' in r and 'Mapa vocal' in r and 'Mais opções' in r, 'tour: mostra as funções atuais (Hoje, Tocar, Mapa vocal, Mais opções)', str(r))
    r = pg.evaluate("()=>{const l=S.lists.find(x=>x.songIds.length>1);vmGo(l.songIds[0],l.id);const a=!!document.querySelector('.bkr');nav(1);const b=S.vw;S.tab='lists';S.hide=false;R();return[a,b]}")
    ok(r[0] and r[1] == 'vocal', 'mapa vocal: tem botão de voltar e as próximas músicas abrem no mapa vocal', str(r))
    r = pg.evaluate("""async()=>{const ctx=new OfflineAudioContext(2,44100,44100),b=ctx.createBuffer(2,44100*20,44100);for(let c=0;c<2;c++){const d=b.getChannelData(c);for(let i=0;i<d.length;i++)d[i]=Math.sin(i*2*Math.PI*440/44100)*.5}
     let ticks=0;const iv=setInterval(()=>ticks++,10);const t0=performance.now();const o=await fxPitchShiftBuffer(b,2,ctx);clearInterval(iv);const d=o.getChannelData(0);let bad=0;for(let i=0;i<d.length;i+=997)if(!isFinite(d[i]))bad++;return{len:o.length==b.length,bad,ticks,ms:Math.round(performance.now()-t0)}}""")
    ok(r['len'] and r['bad'] == 0 and r['ticks'] > 2, 'stems: troca de tom processa em pedaços sem travar a tela', str(r))
    r = pg.evaluate("()=>{const l=S.lists.find(x=>x.songIds.length>1);vmGo(l.songIds[1],l.id);stage(l.id);const a=[S.vw,S.sel==l.songIds[1]];nav(-1);a.push(S.vw);fsExit();vw('cifra');stage(l.id);a.push(S.vw);nav(1);a.push(S.vw);fsExit();S.vw='mapa';S.tab='lists';S.hide=false;R();return a}")
    ok(r == ['vocal', True, 'vocal', 'cifra', 'cifra'], 'modo palco: abre e navega na visão atual (mapa vocal / cifra)', str(r))
    r = pg.evaluate("()=>{const l=S.lists.find(x=>x.songIds.length>1);stage(l.id);stg();const z0=S.z,v=!document.getElementById('stz').hidden;stZ(1);const a=S.z>z0;stZ(-1);fsExit();stg();const h=document.getElementById('stz').hidden;S.tab='lists';S.hide=false;R();return[v,a,h]}")
    ok(r == [True, True, True], 'modo palco: botões A−/A+ mudam o tamanho da letra e somem ao sair', str(r))
    r = pg.evaluate("""async()=>{const w=ms=>new Promise(r=>setTimeout(r,ms));document.querySelectorAll('dialog[open]').forEach(d=>d.close());await w(80);cfgD();const a=[!!$('#cfgRoot .cfp'),!!$('#cfgRoot .cfq'),document.querySelectorAll('#cfgRoot .cfg').length>=3,document.querySelectorAll('#cfgRoot .swt').length>=2];
     cfQ('campo harmonico');a.push([...document.querySelectorAll('#cfgRoot .cfr')].filter(x=>!x.hidden).length);cfQ('zzzz');a.push(!$('#cfno').hidden);cfQ('');
     privD();await w(150);const bk=dlg.querySelector('.dback');a.push(!!bk);if(bk)bk.click();await w(150);a.push(!!$('#cfgRoot'),!dlg.querySelector('.dback'));dlg.close();await w(80);return a}""")
    ok(r == [True, True, True, True, 1, True, True, True, True], 'ajustes: lista agrupada, perfil, busca e subpágina com voltar', str(r))
    r = pg.evaluate("""()=>{ask('Apagar?',()=>{},'Apagar');const a=[d2.dataset.k,!!d2.querySelector('#y2')];d2.close();say('Pronto');a.push(d2.dataset.k);d2.close();const l=S.lists.find(x=>x.songIds.length);sgMenu(l.songIds[0],l.id);a.push(d2.dataset.k,d2.querySelectorAll('.mni').length,!!d2.querySelector('.mcn'));d2.close();return a}""")
    ok(r == ['alert', True, 'alert', 'sheet', 6, True], 'pop-ups: alerta (ask/say) e folha de ações têm o jeito certo', str(r))
    r = pg.evaluate("()=>{if(FS)fsApply(false);const l=S.lists.find(x=>x.songIds.length>1);S.vw='cifra';S.deg=1;S.tab='songs';S.sel=l.songIds[1];S.ctx=l.id;S.hide=true;R();const sv=JSON.parse(localStorage.getItem('rep.ui'));S.vw='mapa';S.deg=0;S.tab='hoje';S.sel='';S.ctx=null;S.hide=false;const ok1=uiRest();const a=[sv.vw,sv.deg,ok1,S.vw,S.deg,S.tab,S.sel==l.songIds[1],S.ctx==l.id];const o=JSON.parse(localStorage.getItem('rep.ui'));o.t=Date.now()-7*36e5;localStorage.setItem('rep.ui',JSON.stringify(o));S.tab='hoje';a.push(uiRest());S.vw='mapa';S.deg=0;S.tab='lists';S.hide=false;S.ctx=null;R();localStorage.removeItem('rep.ui');return a}")
    ok(r == ['cifra', 1, 1, 'cifra', 1, 'songs', True, True, 0], 'lembra a visão e a última tela (e esquece depois de 6 horas)', str(r))
    r = pg.evaluate("""()=>{const a=document.createElement('audio');a.id='vqa';a.dataset.ou='https://x.test/m.mp3';document.body.appendChild(a);Object.defineProperty(a,'duration',{value:240,configurable:true});Object.defineProperty(a,'currentTime',{value:75,writable:true,configurable:true});a.dispatchEvent(new Event('timeupdate'));
     const sv=JSON.parse(localStorage.getItem('rep.pos'))['https://x.test/m.mp3'];a.currentTime=0;a.dispatchEvent(new Event('loadedmetadata'));const r=a.currentTime;a.remove();localStorage.removeItem('rep.pos');return[sv&&sv.s,r]}""")
    ok(r == [75, 75], 'player: retoma a música de onde parou', str(r))
    r = pg.evaluate("()=>{const l=nextL();if(!l.songIds.length)l.songIds=[S.songs[0].id];const s=S.songs.find(x=>x.id==l.songIds[0]);const old=s.vs;s.vs={url:'https://x.test/vs.mp3',name:'vs'};S.tab='hoje';R();const b=document.querySelector('.hjb .offb2');const t=b&&b.textContent;s.vs=old;S.tab='lists';R();return t}")
    ok(r == 'Baixar para offline', 'Hoje: botão Baixar para offline aparece quando há áudio', str(r))
    r = pg.evaluate("""async()=>{const l=nextL(),o=[l.hBanda,l.hGain,l.passHora,l.passFim,l.date,l.hCrtv];l.hCrtv='';l.hBanda='07:00';l.hGain='07:30';l.passHora='07:45';l.passFim='08:10';l.date='2099-05-10';
     const w=document.createElement('div');w.innerHTML=tlV(l,td());const a=[w.querySelectorAll('.tll li').length,w.querySelector('.tlt').textContent,w.querySelectorAll('li.pas').length,w.querySelector('.tls').textContent];
     a.push(tlSt({k:'pas',s:465,e:490},0,400),tlSt({k:'pas',s:465,e:490},0,470),tlSt({k:'pas',s:465,e:490},0,500),tlSt({k:'pas',s:465},5,0),tlSt({k:'pas',s:465},-1,0));
     a.push(typeof tlIcs=='undefined',!/Agenda/.test(w.innerHTML));
     [l.hBanda,l.hGain,l.passHora,l.passFim,l.date,l.hCrtv]=o;return a}""")
    ok(r == [3, '07:45 – 08:10', 1, 'Em 2099 dias'.replace('2099', str(r[3]).split(' ')[1]) if isinstance(r[3], str) and r[3].startswith('Em ') else r[3], 'up', 'now', 'done', 'up', 'done', True, True], 'horários do culto: linha do tempo, passagem em destaque e estados (sem botão de Agenda)', str(r))
    r = pg.evaluate("()=>{S.tab='esc';R();const a=[S.tab,document.querySelectorAll('[data-t=\"esc\"]').length,typeof vEsc];S.tab='lists';R();return a}")
    ok(r == ['hoje', 0, 'undefined'], 'menu Escala removido (sem botão, sem tela)', str(r))
    r = pg.evaluate("""()=>{const T=td(),l=S.lists.filter(x=>x.date&&x.date>=T).sort((a,b)=>a.date.localeCompare(b.date))[0];const ob=l.banda,od=DISP_ALL;l.banda={...(l.banda||{}),vm:'Ana Teste',vf:'Bia Teste',so:'Cris Teste'};DISP_ALL={[l.id]:[{nome:'Ana Teste',status:'sim',obs:''},{nome:'Bia Teste',status:'nao',obs:'viagem'}]};S.tab='dash';R();
     const e=document.querySelector('.dsm'),t=document.querySelector('.dtm'),c=[...document.querySelectorAll('.dtc b')].map(x=>x.textContent),a=[!!e,!!e&&/pendência|Tudo pronto/.test(e.querySelector('.dsq').textContent),c.join(','),!!t&&/viagem/.test(t.textContent),!!t&&/Cris Teste/.test(t.textContent),!/músicas diferentes no período/.test(document.body.textContent),document.querySelectorAll('.dk[onclick]').length>=1];DISP_ALL=od;l.banda=ob;S.tab='lists';R();return a}""")
    ok(r[:2] == [True, True] and r[2].startswith('1,1,') and r[3:] == [True, True, True, True], 'painel: resumo do próximo culto, pendências e confirmação da equipe', str(r))
    r = pg.evaluate("""()=>{const a=[];let w=0;toastA('x','Desfazer',()=>w=1);const b=document.querySelector('#tt.act button');a.push(!!b);if(b)b.click();a.push(w==1,!document.querySelector('#tt').classList.contains('act'));
     const l=cl(S.lists[0]);l.id='tst-del';l.date='2099-01-01';S.lists.push(l);delList('tst-del');a.push(!S.lists.some(x=>x.id=='tst-del'),!d2.open);uDo();a.push(S.lists.some(x=>x.id=='tst-del'));S.lists=S.lists.filter(x=>x.id!='tst-del');return a}""")
    ok(r == [True, True, True, True, True, True], 'desfazer em vez de confirmar: excluir repertório não pergunta e volta com Desfazer', str(r))
    r = pg.evaluate("""()=>{const a=[],id=S.songs[0].id;try{localStorage.removeItem('rep.dr')}catch(e){}editSong(id);D.title+=' RASC';drfNow();const dr=JSON.parse(localStorage.getItem('rep.dr')||'null');a.push(!!dr&&dr.k=='s'&&dr.id==id,!!dlg.querySelector('.drfi'));D0='';dlg.close();
     editSong(id);const b=document.querySelector('#tt.act button');a.push(!!b&&/Restaurar/.test(b.textContent));if(b)b.click();a.push(/ RASC$/.test(D.title));D0='';dlg.close();drfClr();return a}""")
    ok(r == [True, True, True, True], 'rascunho automático: guarda a edição e oferece restaurar', str(r))
    r = pg.evaluate("""()=>{const s=S.songs.find(x=>(x.vmap||[]).length)||S.songs[0];s.vmap=s.vmap||[];s.vmap.push({t:'Que eu passo con8go',h:0,v:'f'},{t:'Mais    de Ti',h:0,v:''});const n=fixCount()[2];fixGo();const t=s.vmap.map(r=>r.t);return [n>=2,t.includes('Que eu passo contigo'),t.includes('Mais de Ti'),fixCount()[2]==0]}""")
    ok(r == [True, True, True, True], 'correção de grafia dos mapas vocais (con8go → contigo)', str(r))
    r = pg.evaluate("""()=>{const s=S.songs.find(x=>(x.vmap||[]).length)||S.songs[0];s.vmap.push({t:'Minha gra@dão e con8go',h:0,v:''});R();const t=s.vmap[s.vmap.length-1].t;s.vmap.pop();return t}""")
    ok(r == 'Minha gratidão e contigo', 'grafia dos mapas corrigida automaticamente ao abrir', str(r))
    r = pg.evaluate("""()=>{const a=[];const l=S.lists.find(x=>x.songIds.length)||S.lists[0];const was=l.apv;S.band=false;ME='Teste';apvSend(l.id);dlg.close&&0;d2.close&&d2.close();apvSet(l.id,'ok');apvD();const h=l.apv.h.map(x=>x.e).join();const txt=dlg.textContent;a.push(h=='env,ok',/Histórico de aprovações/.test(txt),/Aprovado/.test(txt),/Teste/.test(txt));dlg.close();l.apv=was;if(!was)delete l.apv;return a}""")
    ok(r == [True, True, True, True], 'histórico de aprovações da liderança registra envio e resposta', str(r))
    r = pg.evaluate("""()=>{const a=[];a.push(/skl/.test(skl()));const s0=S.songs[0];S.band=false;spotD();$('#spq').value=s0.title.split(' ')[0];spR();a.push(/class="it"/.test($('#spr').innerHTML));$('#spq').value='zzzxqq';spR();a.push(/Nada encontrado/.test($('#spr').innerHTML));dlg.close();
     spM(s0.id);a.push(/Abrir/.test(dlg.innerHTML)&&/Adicionar ao repertório/.test(dlg.innerHTML));dlg.close();
     const l=S.lists.find(x=>x.date&&x.date>=td());if(l){const n=l.songIds.length,had=l.songIds.includes('__x');S.songs.push({id:'__x',title:'X',parts:[],key:'C'});lAddS(l.id,'__x');a.push(l.songIds.length==n+1);l.songIds.pop();S.songs.pop();R()}else a.push(true);
     themeSet('light');a.push(document.documentElement.classList.contains('ltm'));themeSet('dark');a.push(!document.documentElement.classList.contains('ltm'));
     a.push(!!document.getElementById('offb'));return a}""")
    ok(r == [True]*8, 'camada Apple: skeleton, busca única, menu de segurar, adicionar ao repertório, tema, offline', str(r))
    r = pg.evaluate("""()=>{const l=S.lists.find(x=>x.songIds.length>2);S.band=false;vmGo(l.songIds[1],l.id);const a=S.sel,el=document.querySelector('.hd')||document.querySelector('#m');const send=(t,x,y)=>{const T=new Touch({identifier:1,target:el,clientX:x,clientY:y});el.dispatchEvent(new TouchEvent(t,{touches:t=='touchend'?[]:[T],changedTouches:[T],bubbles:true,cancelable:true}))};send('touchstart',300,300);send('touchend',120,310);const b=S.sel;S.tab='lists';R();return [a==l.songIds[1],b==l.songIds[2]]}""")
    ok(r == [True, True], 'deslizar troca exatamente uma música por gesto', str(r))
    r = pg.evaluate("""()=>{const a=[];S.band=false;cfgD();const R=document.querySelector('#cfgRoot');const hs=[...R.querySelectorAll('.cfh')].map(x=>x.textContent);a.push(['Leitura','Aparência','Liderança','Dados e segurança','Conta','Ajuda','Este aparelho'].every(x=>hs.includes(x)));
      cfQ('tema');a.push([...R.querySelectorAll('.cfr:not([hidden])')].some(x=>/Aparência/.test(x.textContent)));
      cfQ('lideran');a.push(R.querySelectorAll('.cfr:not([hidden])').length>=3);
      cfQ('zzzxxqq');a.push(!document.querySelector('#cfno').hidden);cfQ('');a.push(R.querySelectorAll('.cfr[hidden]').length==0);dlg.close();return a}""")
    ok(r == [True]*5, 'Ajustes: seções claras e busca com sinônimos', str(r))
    r = pg.evaluate("""()=>{const a=[];const l=S.lists.find(x=>x.songIds.length>1);const keep=l.songIds[0];l.cant=l.cant||{};l.ord=l.ord||{};l.cant['__fantasma']='X';l.ord['__fantasma']='9';l.cant[keep]=l.cant[keep]||'Fulano';a.push(orphN()>=2);R();a.push(!('__fantasma' in l.cant)&&!('__fantasma' in l.ord));a.push(!!l.cant[keep]);return a}""")
    ok(r == [True, True, True], 'limpeza automática de sobras (quem canta/ordem/tom de músicas que saíram do repertório)', str(r))
    r = pg.evaluate("""()=>{const a=[];const n0=fixCount();a.push(Array.isArray(n0));const s=S.songs.find(x=>x.id=='s91');const had=s?[...(s.tags||[])]:null;
     if(s){s.tags=(s.tags||[]).filter(x=>!/^(Vertical|Horizontal)$/i.test(x))}const n1=fixCount();a.push(!s||n1[0]>=1);fixGo();a.push(!s||hasT(s,'Vertical'));const n2=fixCount();a.push(n2[0]==0&&n2[1]==0);uDo();const s2=S.songs.find(x=>x.id=='s91');a.push(!s2||!hasT(s2,'Vertical'));
     if(s2)s2.tags=had;return a}""")
    ok(r == [True, True, True, True, True], 'correções de dados: conta, aplica só o que está vazio e deixa desfazer', str(r))
    r = pg.evaluate("""async()=>{const l=S.lists.find(x=>x.songIds.length);window.__pb=null;const o=window.claude&&window.claude.use;window.claude=window.claude||{};window.claude.use=async k=>k=='downloads'?{save:async a=>{window.__pb=new Uint8Array(a.data)}}:(o?o.call(window.claude,k):{});
     await pdfL(l.id);const b=window.__pb;if(o)window.claude.use=o;return b?[String.fromCharCode(...b.slice(0,5)),b.length>5000,(new TextDecoder('latin1').decode(b).match(/\\/Type\\s*\\/Page[^s]/g)||[]).length>=2]:null}""")
    ok(r == ['%PDF-', True, True], 'PDF do repertório: gera um arquivo válido com capa e uma página por música', str(r))
    r = pg.evaluate("""()=>{const a=[];S.band=false;const v=verN();a.push(v.fix.length==4&&v.info.length==4);const l=S.lists.find(x=>x.songIds.length>1);l.cant=l.cant||{};l.cant['__fantasma']='X';a.push(verN().fix[3][1]>=1);verD();a.push(/Verificar dados/.test(dlg.innerHTML)&&/Corrigir tudo/.test(dlg.innerHTML));verGo();a.push(!('__fantasma' in l.cant));a.push(verN().fix[3][1]==0);dlg.close();d2.close&&d2.close();return a}""")
    ok(r == [True]*5, 'Verificar dados: lista pendências e corrige tudo com um toque', str(r))
    # 5a) resumo de erros dos aparelhos (item 10)
    r = pg.evaluate("""async()=>{const a=[];const now=new Date().toISOString(),old=new Date(Date.now()-30*864e5).toISOString();
     const w=errSum([{msg:'A',vezes:7,ultima:now},{msg:'B',vezes:1,ultima:now},{msg:'C',vezes:9,ultima:old}],7);a.push(w.n==2,w.rep.length==1,w.v==8);
     const o=window.__SB;S.band=false;S.role='dono';localStorage.removeItem('rep.errday');localStorage.removeItem('rep.errwk');
     window.__SB={from:()=>({select:()=>({order:()=>({limit:async()=>({data:[{msg:'Falha X',vezes:6,ultima:now}],error:null})})})})};
     const d=await errResumo();a.push(!!d&&/Erro repetido 6/.test(document.querySelector('#tt').textContent));
     localStorage.setItem('rep.errday',String(Date.now()));localStorage.removeItem('rep.errwk');
     window.__SB={from:()=>({select:()=>({order:()=>({limit:async()=>({data:[{msg:'Y',vezes:1,ultima:now}],error:null})})})})};
     await errResumo(1);a.push(/Resumo da semana/.test(document.querySelector('#tt').textContent));
     window.__SB=o;return a}""")
    ok(r == [True]*5, 'resumo de erros: soma da semana e alerta de erro repetido', str(r))
    # 5a2) gestos: segurar numa música abre o menu; mexer o dedo cancela
    r = pg.evaluate("""async()=>{const a=[];S.band=false;S.tab='songs';S.sel=null;R();await new Promise(r=>setTimeout(r,200));const el=document.querySelector('#ls .it');if(!el)return['sem lista'];
     const ev=(t,x,y)=>el.dispatchEvent(new PointerEvent(t,{pointerType:'touch',clientX:x,clientY:y,bubbles:true,cancelable:true}));
     ev('pointerdown',100,100);await new Promise(r=>setTimeout(r,700));a.push(dlg.open&&/Adicionar ao repertório|Abrir/.test(dlg.innerHTML));ev('pointerup',100,100);dlg.close();
     ev('pointerdown',100,100);ev('pointermove',100,160);await new Promise(r=>setTimeout(r,700));a.push(!dlg.open);ev('pointerup',100,160);
     ev('pointerdown',100,100);await new Promise(r=>setTimeout(r,200));ev('pointerup',100,100);await new Promise(r=>setTimeout(r,500));a.push(!dlg.open);
     el.dispatchEvent(new MouseEvent('contextmenu',{bubbles:true,cancelable:true}));a.push(dlg.open);dlg.close();return a}""")
    ok(r == [True]*4, 'gestos: segurar abre o menu; arrastar ou toque curto não abrem', str(r))
    # 5a3) visual: sem rolagem lateral nem elementos para fora da tela; compara capturas com a referência (aviso, não derruba)
    pg.clock.set_fixed_time('2026-11-06T15:00:00Z')  # data fixa: as telas mostram 'hoje/amanhã' e não podem mudar com o calendário
    VD = os.path.join(HERE, 'visual'); os.makedirs(os.path.join(VD, 'base'), exist_ok=True); os.makedirs(os.path.join(VD, 'atual'), exist_ok=True)
    telas = {'musica': "S.tab='songs';S.sel=S.songs.find(x=>(x.vmap||[]).length)?.id||S.songs[0].id;S.vw='mapa'", 'lista': "S.tab='songs';S.sel=null", 'repertorio': "S.tab='lists';S.lv=(S.lists.find(x=>x.songIds.length)||S.lists[0]).id;S.lvm=1", 'ajustes': "S.tab='songs';S.sel=null"}
    for nome, js in telas.items():
        pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d=>d.close());S.band=false;" + js + (";R();cfgD()" if nome == 'ajustes' else ";R()")); pg.wait_for_timeout(500); pg.evaluate("(()=>{const t=document.getElementById('tt');if(t)t.classList.remove('on','act')})()")  # aviso (toast) de testes anteriores não entra na captura
        g = pg.evaluate("""()=>{const W=innerWidth,bad=[];document.querySelectorAll('body *').forEach(e=>{if(!e.offsetParent&&getComputedStyle(e).position!='fixed')return;const r=e.getBoundingClientRect();if(r.width&&r.right>W+2&&!e.closest('[class*=scr],.tabs,#tbb,pre,table,.hscroll,svg,canvas,dialog,[style*=overflow]')&&getComputedStyle(e).position!='fixed')bad.push((e.tagName+'.'+(e.className&&e.className.baseVal===undefined?e.className:'')).slice(0,40))});return{sw:document.documentElement.scrollWidth-W,bad:bad.slice(0,4)}}""")
        ok(g['sw'] <= 1, f'visual {nome}: sem rolagem lateral (390 px)', str(g))
        arq = nome + '.png'; pg.screenshot(path=os.path.join(VD, 'atual', arq))
        bp = os.path.join(VD, 'base', arq)
        try:
            from PIL import Image, ImageChops
            if os.path.exists(bp):
                A = Image.open(bp).convert('RGB'); Bm = Image.open(os.path.join(VD, 'atual', arq)).convert('RGB')
                if A.size != Bm.size: print(f'⚠ visual {nome}: tamanho da captura mudou {A.size} → {Bm.size}'); continue
                dif = ImageChops.difference(A, Bm).convert('L').point(lambda v: 255 if v > 24 else 0); pct = sum(1 for v in dif.getdata() if v) / (A.size[0] * A.size[1]) * 100
                if pct > 2: print(f'⚠ visual {nome}: {pct:.1f}% da tela mudou em relação à referência'); (FAIL.append('visual ' + nome) if os.environ.get('VISUAL_ESTRITO') else None)
        except ImportError: pass
    r = pg.evaluate("""()=>{const a=[];S.band=false;const l={id:'__mm',date:'2099-03-01',place:'Mauá',turno:'Manhã',name:'Culto de Domingo',songIds:[],banda:{}};
     a.push(tecK(l)=='mm');tecFill(l);a.push([l.hCrtv,l.hBanda,l.hGain,l.passHora,l.passFim].join()=='07:20,07:30,07:30,07:40,08:10');
     const n={id:'__mn',date:'2099-03-10',place:'Mauá',turno:'Noite',name:'Reunião',songIds:[],banda:{}};tecFill(n);a.push(tecK(n)==''&&!n.hCrtv&&!n.hBanda);
     const sa={id:'__sa',date:'2099-03-08',place:'Santo André',turno:'Manhã',name:'Culto de Domingo',songIds:[],banda:{}};tecFill(sa);a.push(sa.hBanda=='07:30'&&sa.passHora=='07:45'&&!sa.hCrtv);
     const o={id:'__mo',date:'2099-03-15',place:'Mauá',turno:'Manhã',name:'Ceia',songIds:[],banda:{},hBanda:'07:00',hGain:'07:30',passHora:'07:45',passFim:'08:10'},pas={id:'__mp',date:'2000-01-01',place:'Mauá',turno:'Manhã',name:'Antigo',songIds:[],banda:{},hBanda:'07:00'};
     S.lists.push(o,pas);const was=S.mig.mm2;delete S.mig.mm2;mm1();a.push([o.hCrtv,o.hBanda,o.passHora].join()=='07:20,07:30,07:40'&&pas.hBanda=='07:00'&&!pas.hCrtv&&S.mig.mm2==1);
     a.push(/Chegada CRTV/.test(tecV(o))&&tlItems(o).some(x=>x.k=='crtv'));S.lists=S.lists.filter(x=>!/^__m/.test(x.id));S.mig.mm2=was;return a}""")
    ok(r == [True]*6, 'Mauá manhã: horários padrão da tabela (CRTV 7h20, banda 7h30, passagem 7h40–8h10) e ajuste dos próximos cultos', str(r))
    r = pg.evaluate("""async()=>{const a=[],o=[DISP_ALL,ME_M,MY_DISP,window.__SBB];S.band=false;
     DISP_ALL={'per:2099-12-20:2100-01-05':[{nome:'Ana Teste',status:'nao',obs:'viagem'}]};
     const h=perHit('ANA TESTE','2099-12-25');a.push(!!h&&h.status=='nao'&&/viagem/.test(h.obs)&&h.obs.includes('20/12'));a.push(perHit('Ana Teste','2100-01-06')===null&&perHit('Outro','2099-12-25')===null);
     const l={id:'__pe',date:'2099-12-25',place:'Mauá',turno:'Noite',name:'Culto',songIds:[],banda:{vm:'Ana Teste'}};DISP_ALL['__pe']=[{nome:'Ana Teste',status:'sim',obs:''}];a.push(dispDe('Ana Teste',l).status=='sim');delete DISP_ALL['__pe'];a.push(dispDe('Ana Teste',l).status=='nao');
     const calls=[],q={upsert:x=>{calls.push(x);return Promise.resolve({})},delete:()=>q,eq:()=>q,then:f=>f({})};window.__SBB={from:()=>q};ME_M={id:'m1',nome:'Ana Teste'};MY_DISP={};
     S.band=false;S.tab='perf';R();a.push(!!document.querySelector('.perc'));
     document.querySelector('#per_de').value='2099-12-20';document.querySelector('#per_ate').value='2099-12-22';document.querySelector('#per_obs').value='viagem';await perAdd();
     a.push(calls.length==1&&calls[0].culto_id=='per:2099-12-20:2099-12-22'&&calls[0].status=='nao'&&perMine().length==1);
     [DISP_ALL,ME_M,MY_DISP,window.__SBB]=o;S.tab='lists';R();const tt=document.querySelector('#tt');if(tt)tt.classList.remove('on');return a}""")
    ok(r == [True]*6, 'indisponibilidade por período: perfil grava, aviso cobre as datas e o culto respondido vale mais', str(r))
    r = pg.evaluate("""()=>{const a=[],T=td(),d=n=>{const x=new Date(T+'T12:00');x.setDate(x.getDate()-n);return x.toISOString().slice(0,10)};
     const s1=S.songs[0],s2=S.songs[1],s3=S.songs[2],o=S.lists;S.lists=[{id:'__a',date:d(200),songIds:[s1.id],banda:{}},{id:'__b',date:d(10),songIds:[s2.id],banda:{}},{id:'__c',date:d(5),songIds:[s2.id],banda:{}}];
     P={id:'__n',songIds:[],banda:{},q:''};document.body.insertAdjacentHTML('beforeend','<div id="pkf"></div><div id="pk"></div>');PKF='old';pkR();const has=(id)=>document.querySelector('#pk').innerHTML.includes("la('"+id+"')");a.push(has(s1.id)&&!has(s2.id));
     PKF='new';pkR();a.push(!has(s1.id)&&!has(s2.id)&&has(s3.id));
     PKF='top';pkR();a.push(has(s2.id)&&!has(s3.id)&&has(s1.id));
     PKF='';S.lists=o;document.querySelector('#pk').remove();document.querySelector('#pkf').remove();P=null;return a}""")
    ok(r == [True]*3, 'sugestões ao escolher músicas: sem tocar há 2+ meses, nunca tocadas e mais tocadas', str(r))
    r = pg.evaluate("""()=>{const a=[],o=[S.tab,S.lv,S.lvm,S.sel,S.hide,S.ctx,S.band];S.band=false;document.querySelectorAll('dialog[open]').forEach(d=>d.close());
     const l=S.lists.find(x=>x.songIds.length&&x.date);S.tab='lists';S.lv=l.id;S.lvm=1;R();const b=document.querySelector('#nvb');
     a.push(!b.hidden&&/Repertórios/.test(b.textContent)&&document.body.classList.contains('tbon'));        // detalhe do culto: Voltar + menu fixo
     S.tab='songs';S.ctx=l.id;S.sel=l.songIds[0];S.hide=true;R();a.push(!b.hidden&&/Culto/.test(b.textContent)&&document.body.classList.contains('tbon'));   // música: menu fixo
     bkGo();a.push(S.tab=='lists'&&S.lv==l.id&&!S.ctx);                                                  // Voltar leva ao culto
     bkGo();a.push(S.lvm==0&&b.hidden);                                                                  // e depois à lista
     S.tab='hoje';R();S.tab='perf';R();a.push(!b.hidden&&/Hoje/.test(b.textContent));bkGo();a.push(S.tab=='hoje');
     FS=true;uiPost();a.push(b.hidden&&!document.body.classList.contains('tbon'));FS=false;                 // Palco: sem menu e sem Voltar
     [S.tab,S.lv,S.lvm,S.sel,S.hide,S.ctx,S.band]=o;R();return a}""")
    ok(r == [True]*7, 'navegação: menu fixo em todas as telas (menos no Palco) e botão Voltar no topo', str(r))
    r = pg.evaluate("""()=>{const a=[];S.band=false;const o=S.lists;editList(null);a.push(!!document.querySelector('.ltb [data-lt="rs"]'));
     ltG('ev');ltS(1);a.push(LTB=='ev');const sy=dlg.querySelector('.ltb .tb[data-lt="ev"]');Object.assign(P,{name:'Culto',date:'2099-05-05',place:'Mauá',turno:'Noite'});ltS(1);a.push(LTB=='eq'&&!document.querySelector('#lvt').hidden&&/Passo 2 de 7/.test(document.querySelector('#lsh').textContent)&&document.querySelector('.ltb .tb[data-lt="ev"]').classList.contains('ok'));ltG('pa');a.push(document.querySelector('#lnx').hidden===false);ltS(1);a.push(LTB=='rs'&&document.querySelector('#lnx').hidden&&/Resumo antes de salvar/.test(document.querySelector('#rsw').textContent));
     ltG('ev');a.push(document.querySelector('#lvt').hidden);dlg.close();return a}""")
    ok(r == [True]*6, 'culto em passos: Próxima/Voltar percorre as etapas até o Resumo', str(r))
    r = pg.evaluate("""()=>{const a=[];const mk=(d,t,n)=>({id:'__q'+d,date:d,place:'Mauá',turno:t,name:n,songIds:[],banda:{}});
     const dn=mk('2099-03-01','Noite','Culto de Domingo'),qu=mk('2099-03-05','Noite','Culto de Quinta'),qs=mk('2099-03-05','','Culto');[dn,qu,qs].forEach(tecFill);
     a.push([dn.hCrtv,dn.hBanda,dn.hGain,dn.passHora,dn.passFim].join()=='16:50,17:00,17:00,17:10,17:40');
     a.push([qu.hCrtv,qu.hBanda,qu.hGain,qu.passHora,qu.passFim].join()=='18:30,18:40,18:40,18:50,19:20',qs.hCrtv=='18:30');
     const sx=mk('2099-03-03','Noite','Reunião');tecFill(sx);a.push(!sx.hBanda&&tecK(sx)==='');
     const f={id:'__qf',date:'2099-06-04',place:'Mauá',turno:'Noite',name:'Quinta',songIds:[],banda:{},hBanda:'19:00',passHora:'19:10'},d2={id:'__qg',date:'2099-06-07',place:'Mauá',turno:'Noite',name:'Domingo',songIds:[],banda:{}};
     S.lists.push(f,d2);const was=S.mig.mm2;delete S.mig.mm2;mm1();a.push(f.hBanda=='18:40'&&f.passFim=='19:20'&&d2.hCrtv=='16:50');S.lists=S.lists.filter(x=>!/^__q/.test(x.id));S.mig.mm2=was;return a}""")
    ok(r == [True]*5, 'Mauá: tabelas de quinta (18h30) e domingo à noite (18h30) viram padrão e ajustam os próximos cultos', str(r))
    r = pg.evaluate("""async()=>{const a=[];S.band=false;localStorage.removeItem('rep.stzm');localStorage.setItem('rep.stgp','1');S.z=1;
     let rel=0;const lk={release:async()=>{rel++},addEventListener(){}};let req=0;Object.defineProperty(navigator,'wakeLock',{configurable:true,value:{request:async()=>{req++;return lk}}});
     const l=S.lists.find(x=>x.songIds.length>2);stage(l.id);await new Promise(r=>setTimeout(r,300));
     a.push([FS,req].join()=="true,1");                                 // 0: tela acesa
     a.push(document.getElementById('stg')&&!document.getElementById('stg').hidden&&!!document.querySelector('#stg .stp'));   // 1: botão fixar
     toast('teste');toastA('teste','x',()=>{});a.push(!document.querySelector('#tt.on'));      // 2: sem avisos
     const i0=l.songIds.indexOf(S.sel);stNav(1);stNav(1);a.push(l.songIds.indexOf(S.sel)==i0+1);   // 3: toque duplo vale um
     stgT();a.push(stPin()===false);stCol(true);a.push(document.getElementById('stg').classList.contains('col')&&document.body.classList.contains('stgc'));  // 4,5: recolhe
     stOpen();a.push(!document.getElementById('stg').classList.contains('col'));stgT();a.push(stPin()===true);    // 6,7
     const z=S.z;fsExit();await new Promise(r=>setTimeout(r,200));a.push(FS===false&&!NSV);   // 8: sai do Palco sem sobras
     toast('depois');a.push(!!document.querySelector('#tt.on'));    // 9: avisos voltam fora do Palco
     delete navigator.wakeLock;WL=null;S.tab='lists';S.lv=null;R();return a.concat([z])}""")
    ok(r[:10] == [True]*10, 'Palco: tela acesa, barra fixável/recolhível, toque duplo protegido, sem avisos por cima da cifra', str(r))
    r = pg.evaluate("""async()=>{const a=[];S.band=false;Object.defineProperty(navigator,'wakeLock',{configurable:true,value:undefined});const l=S.lists.find(x=>x.songIds.length>3);stage(l.id);await new Promise(r=>setTimeout(r,300));
     a.push(!!NSV&&NSV.tagName=='VIDEO'&&NSV.muted);                          // sem wakeLock: vídeo mudo mantém a tela acesa
     const el=document.querySelector('#m')||document.body;const go=async(dx,ms)=>{await new Promise(r=>setTimeout(r,600));const el=document.querySelector('#m')||document.body;const i=l.songIds.indexOf(S.sel);const T=(x)=>new Touch({identifier:1,target:el,clientX:x,clientY:300});const f=(t,x)=>el.dispatchEvent(new TouchEvent(t,{touches:t=='touchend'?[]:[T(x)],changedTouches:[T(x)],bubbles:true,cancelable:true}));f('touchstart',300);return new Promise(r=>setTimeout(()=>{f('touchend',300+dx);r(l.songIds.indexOf(S.sel)-i)},ms))};
     stNt=0;a.push(await go(-80,100)==0);                                        // deslize curto: nada
     stNt=0;a.push(await go(-160,100)==1);                                       // deslize firme: uma música
     stNt=0;a.push(await go(-160,700)==0);                                       // deslize lento: nada
     fsExit();await new Promise(r=>setTimeout(r,200));a.push(!NSV);delete navigator.wakeLock;S.tab='lists';S.lv=null;R();return a}""")
    ok(r == [True]*5, 'Palco: sem a função de tela acesa usa o vídeo mudo; só deslize firme e rápido troca de música', str(r))
    # 5b) varredura: percorre todas as telas e diálogos principais; qualquer erro de JavaScript derruba o teste
    E0 = len(E); pg.on('console', lambda m: E.append('console: ' + m.text[:160]) if m.type == 'error' and 'supabase' not in m.text.lower() and 'Failed to load resource' not in m.text else None)
    steps = pg.evaluate("""async()=>{const fails=[];let n=0;const T=async(name,f)=>{n++;try{await f()}catch(e){fails.push(name+': '+String(e).slice(0,100))}
      document.querySelectorAll('dialog[open]').forEach(d=>{try{d.close()}catch(e){}});await new Promise(r=>setTimeout(r,40))};
     const sg=S.songs.find(x=>(x.parts||[]).length)||S.songs[0],ls=S.lists.find(x=>x.songIds.length)||S.lists[0];
     for(const t of ['hoje','esp','lists','songs','perf','dash']){await T('aba '+t,()=>{S.tab=t;S.sel=null;S.lv=null;R()})}
     for(const dark of ['light','dark','auto']){await T('tema '+dark,()=>{themeSet(dark);R()})}
     await T('música aberta',()=>{S.tab='songs';S.sel=sg.id;R()});
     for(const m of ['mapa','cifra','vocal'])await T('modo '+m,()=>{S.vw=m;R()});
     await T('editar música',()=>editSong(sg.id));
     await T('menu da música',()=>{const b=document.querySelector('[onclick*="amq"],.amq');R()});
     await T('repertório aberto',()=>{S.tab='lists';S.lv=ls.id;S.lvm=1;R()});
     await T('repertório em lista',()=>{S.lvm=0;R()});
     await T('palco',()=>{stage(ls.id)});
     await T('PDF do repertório (diálogo)',()=>{typeof lpdfD=='function'&&lpdfD(ls.id)});
     await T('aprovação',()=>apvD&&apvD());
     await T('ajustes',()=>cfgD());
     for(const q of ['tema','lideran','dados','conta','zzz',''])await T('busca ajustes '+q,()=>{cfgD();cfQ(q)});
     await T('verificar dados',()=>{fixCount()});
     await T('busca global',()=>spotD());
     await T('sobre/ajuda',()=>{typeof helpD=='function'&&helpD()});
     for(const b of [...document.querySelectorAll('.tabs button[data-t],#tbb [data-t]')])await T('botão '+b.dataset.t,()=>b.click());
     S.tab='hoje';S.sel=null;S.lv=null;R();return{n,fails}}""")
    ok(not steps['fails'] and steps['n'] > 30, f"varredura de telas: {steps['n']} passos sem erro", '; '.join(steps['fails'][:4]))
    pg.wait_for_timeout(300); ok(len(E) == E0, 'varredura de telas: nenhum erro novo de JavaScript', '; '.join(E[E0:E0+3]))
    # 6) proteção contra código malicioso nos textos
    pg.evaluate("(x)=>{const s=S.songs[0];s.title+=x;s.artist=(s.artist||'')+x;s.nota=x;const l=S.lists.find(l=>l.songIds.length);l.pregador=x;l.name=(l.name||'')+x;(l.cant=l.cant||{})[l.songIds[0]]=x;S.tab='lists';S.lv=l.id;S.lvm=1;R()}", XSS)
    pg.wait_for_timeout(300); pg.evaluate("S.tab='songs';S.sel=S.songs[0].id;R()"); pg.wait_for_timeout(300); pg.evaluate("S.tab='dash';R()"); pg.wait_for_timeout(300)
    ok(pg.evaluate('window.__x===undefined'), 'segurança: textos com código não são executados')
    ok(not E, 'admin: sem erros de JavaScript', '; '.join(E[:3])); c.close()
    b.close()
srv.shutdown()
print(f'\n{"TUDO CERTO" if not FAIL else str(len(FAIL)) + " FALHA(S): " + "; ".join(FAIL)}')
sys.exit(1 if FAIL else 0)
