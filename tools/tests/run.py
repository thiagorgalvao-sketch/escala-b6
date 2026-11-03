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

# 1) sintaxe do JavaScript das páginas
for f in ['index.html', 'admin/index.html']:
    s = open(os.path.join(ROOT, f), encoding='utf-8').read()
    for i, sc in enumerate(re.findall(r'<script>([\s\S]*?)</script>', s)):
        t = tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8'); t.write(sc); t.close()
        r = subprocess.run(['node', '--check', t.name], capture_output=True, text=True); os.unlink(t.name)
        ok(r.returncode == 0, f'sintaxe {f} bloco {i+1}', r.stderr[-300:])
for f in ['sw.js', 'tools/shim.js', 'tools/sbshim.js']:
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
    ok(not E, 'banda: sem erros de JavaScript', '; '.join(E[:3])); c.close()

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
    r = pg.evaluate("""async()=>{const l=S.lists.find(x=>x.songIds.length&&x.date);l.date='2099-01-01';delete l.pub;const id=l.id;
     save();await pubSync();const d=await claude.use('db');const q=await d.collection('pub').get();const x=q.docs.find(y=>y.id=='l_'+id);const o=JSON.parse(x.data().j);
     return{n:o.songIds.length,esp:l.songIds.length,pub:true}}""")
    ok(r['n'] == r['esp'] and r['pub'], 'admin: salvar culto futuro já envia as músicas para a banda (sem publicar)', str(r))
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
    lid2 = pg.evaluate("(S.lists.find(l=>l.songIds.length&&l.date)||{}).id")
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
    # 6) proteção contra código malicioso nos textos
    pg.evaluate("(x)=>{const s=S.songs[0];s.title+=x;s.artist=(s.artist||'')+x;s.nota=x;const l=S.lists.find(l=>l.songIds.length);l.pregador=x;l.name=(l.name||'')+x;(l.cant=l.cant||{})[l.songIds[0]]=x;S.tab='lists';S.lv=l.id;S.lvm=1;R()}", XSS)
    pg.wait_for_timeout(300); pg.evaluate("S.tab='songs';S.sel=S.songs[0].id;R()"); pg.wait_for_timeout(300); pg.evaluate("S.tab='esc';R()"); pg.wait_for_timeout(300)
    ok(pg.evaluate('window.__x===undefined'), 'segurança: textos com código não são executados')
    ok(not E, 'admin: sem erros de JavaScript', '; '.join(E[:3])); c.close()
    b.close()
srv.shutdown()
print(f'\n{"TUDO CERTO" if not FAIL else str(len(FAIL)) + " FALHA(S): " + "; ".join(FAIL)}')
sys.exit(1 if FAIL else 0)
