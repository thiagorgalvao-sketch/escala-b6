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
NL = sum(1 for k in PUB if k.startswith('l_'))
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
    pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d=>d.close())")
    n0 = pg.evaluate('S.songs.length')
    pg.evaluate("editSong()"); pg.fill('#nsq', 'cancao de teste'); pg.click('#dlg button:has-text("Buscar")'); pg.wait_for_timeout(800)
    pg.click('#nsr .cbi >> nth=0'); pg.wait_for_timeout(1200)
    d = pg.evaluate("({t:D.title,k:D.key,bpm:D.bpm,n:D.parts.filter(q=>q.chords).length,cc:D.cc})")
    ok(d['k'] == 'A' and d['n'] >= 2 and d['bpm'] == 72, 'admin: nova música pela busca traz cifra, tom, BPM e blocos', str(d))
    pg.evaluate("ssong()"); pg.wait_for_timeout(500); ok(pg.evaluate('S.songs.length') == n0 + 1, 'admin: salvar música nova')
    sid = pg.evaluate("S.songs[0].id"); pg.evaluate(f"editSong('{sid}')"); pg.fill('.etit', 'Alterado'); pg.click('#dlg button:has-text("Cancelar")'); pg.wait_for_timeout(200)
    ok(pg.evaluate("dlg.open&&d2.open"), 'admin: avisa antes de sair sem salvar'); pg.evaluate("d2.close();D0='';dlg.close()")
    # 4) proteção contra código malicioso nos textos
    pg.evaluate("(x)=>{const s=S.songs[0];s.title+=x;s.artist=(s.artist||'')+x;s.nota=x;const l=S.lists.find(l=>l.songIds.length);l.pregador=x;l.name=(l.name||'')+x;(l.cant=l.cant||{})[l.songIds[0]]=x;S.tab='lists';S.lv=l.id;S.lvm=1;R()}", XSS)
    pg.wait_for_timeout(300); pg.evaluate("S.tab='songs';S.sel=S.songs[0].id;R()"); pg.wait_for_timeout(300); pg.evaluate("S.tab='esc';R()"); pg.wait_for_timeout(300)
    ok(pg.evaluate('window.__x===undefined'), 'segurança: textos com código não são executados')
    ok(not E, 'admin: sem erros de JavaScript', '; '.join(E[:3])); c.close()
    b.close()
srv.shutdown()
print(f'\n{"TUDO CERTO" if not FAIL else str(len(FAIL)) + " FALHA(S): " + "; ".join(FAIL)}')
sys.exit(1 if FAIL else 0)
