# Script de varredura visual (não faz parte do CI). Tira screenshots do app em
# mobile e desktop, banda e administração, para revisão de UX/UI/design/layout.
import json, os, re, functools, http.server, threading, tempfile, subprocess
from playwright.sync_api import sync_playwright

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = '/tmp/shots'
os.makedirs(OUT, exist_ok=True)

class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=ROOT))
PORT = srv.server_address[1]; threading.Thread(target=srv.serve_forever, daemon=True).start()
B = f'http://127.0.0.1:{PORT}'

PUB = json.load(open(os.path.join(ROOT, 'pub.json'), encoding='utf-8'))
STUB = open(os.path.join(HERE, 'stub.js'), encoding='utf-8').read()

def ctx_of(b, w, h):
    c = b.new_context(viewport={'width': w, 'height': h}, service_workers='block')
    c.route('**/fonts.googleapis.com/**', lambda r: r.abort())
    c.route('**/i.ytimg.com/**', lambda r: r.abort())
    return c

VP = {'mobile': (390, 844), 'desktop': (1400, 900)}

with sync_playwright() as p:
    b = p.chromium.launch()

    # ===== banda (sem login, dados de pub.json) =====
    for vp, (w, h) in VP.items():
        c = ctx_of(b, w, h); c.route('**/*.supabase.co/**', lambda r: r.fulfill(status=200, content_type='application/json', body='[]'))
        c.add_init_script("try{localStorage.setItem('rep.tour','1');localStorage.setItem('rep.meask','1')}catch(e){}")
        pg = c.new_page(); pg.goto(B + '/'); pg.wait_for_timeout(2500)
        pg.evaluate("recOk((S.esp.rec||[]).map(x=>x.id).join(','));document.querySelectorAll('dialog[open]').forEach(d=>d.close())")
        pg.screenshot(path=f'{OUT}/{vp}_1_repertorios.png', full_page=False)

        lid = pg.evaluate("(S.lists.filter(l=>l.songIds.length&&l.date).sort((a,b)=>b.date.localeCompare(a.date))[0]||{}).id")
        if lid:
            pg.evaluate(f"S.tab='lists';S.lv='{lid}';S.lvm=1;R()"); pg.wait_for_timeout(500)
            pg.screenshot(path=f'{OUT}/{vp}_2_repertorio.png', full_page=False)

            pg.evaluate("document.querySelector('#lvl li[data-id] .it.sc').click()"); pg.wait_for_timeout(500)
            pg.screenshot(path=f'{OUT}/{vp}_3_musica_blocos.png', full_page=False)

            pg.evaluate("S.vw='vocal';R()"); pg.wait_for_timeout(400)
            pg.screenshot(path=f'{OUT}/{vp}_4_mapa_vocal.png', full_page=False)
            pg.evaluate("S.vw='cifra';R()"); pg.wait_for_timeout(400)
            pg.screenshot(path=f'{OUT}/{vp}_5_cifra.png', full_page=False)

            pg.evaluate("S.hide=false;S.ctx=null;S.sel=null;R()"); pg.wait_for_timeout(300)

        pg.evaluate("S.tab='esp';R()"); pg.wait_for_timeout(400)
        pg.screenshot(path=f'{OUT}/{vp}_6_espiritual.png', full_page=False)

        pg.evaluate("S.tab='songs';R()"); pg.wait_for_timeout(400)
        pg.screenshot(path=f'{OUT}/{vp}_7_musicas.png', full_page=False)
        c.close()

    # ===== administração (Supabase simulado + login) =====
    lists = [{'id': k, 'j': v['j']} for k, v in PUB.items()]
    DB = {'users': [{'id': 'u1', 'email': 'adm@teste.local', 'password': 'senha123', 'meta': {'pw_ok': True}}], 'admins': [{'user_id': 'u1', 'email': 'adm@teste.local'}],
          'membros': [], 'config': [], 'disponibilidade': [], 'team': [dict(x, u=1) for x in lists], 'pub': lists}
    for vp, (w, h) in VP.items():
        c = ctx_of(b, w, h)
        c.route('**/vendor/supabase.min.js', lambda r: r.fulfill(status=200, content_type='application/javascript', body=STUB))
        c.route('**/cdn.jsdelivr.net/**supabase**', lambda r: r.fulfill(status=200, content_type='application/javascript', body=STUB))
        c.route('**/*.supabase.co/**', lambda r: r.fulfill(status=200, content_type='application/json', body='[]'))
        c.add_init_script("if(!localStorage.getItem('__seeded')){localStorage.setItem('__seeded','1');localStorage.setItem('__stubdb',%s);localStorage.setItem('adm:rep.tour','1')}" % json.dumps(json.dumps(DB)))
        pg = c.new_page(); pg.goto(B + '/admin/'); pg.wait_for_timeout(1500)
        pg.fill('#b6e', 'adm@teste.local'); pg.fill('#b6p', 'senha123'); pg.click('#b6f button[type=submit]'); pg.wait_for_timeout(5000)
        pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d=>d.close())")
        pg.screenshot(path=f'{OUT}/{vp}_adm_1_repertorios.png', full_page=False)

        lid = pg.evaluate("(S.lists.filter(l=>l.songIds.length&&l.date).sort((a,b)=>b.date.localeCompare(a.date))[0]||{}).id")
        if lid:
            pg.evaluate(f"S.tab='lists';S.lv='{lid}';S.lvm=1;R()"); pg.wait_for_timeout(500)
            pg.screenshot(path=f'{OUT}/{vp}_adm_2_repertorio.png', full_page=False)
            pg.evaluate(f"editList('{lid}')"); pg.wait_for_timeout(500)
            pg.screenshot(path=f'{OUT}/{vp}_adm_3_editar_repertorio.png', full_page=False)
            pg.evaluate("dlg.close()")

        pg.evaluate("S.tab='songs';S.sel=null;S.hide=false;S.ctx=null;R()"); pg.wait_for_timeout(400)
        pg.screenshot(path=f'{OUT}/{vp}_adm_4_musicas.png', full_page=False)
        pg.evaluate("editSong()"); pg.wait_for_timeout(500)
        pg.screenshot(path=f'{OUT}/{vp}_adm_5_nova_musica.png', full_page=False)
        pg.evaluate("d2.close();dlg.close()")

        pg.evaluate("acD()"); pg.wait_for_timeout(600)
        pg.screenshot(path=f'{OUT}/{vp}_adm_6_acesso_banda.png', full_page=False)
        c.close()

    b.close()
srv.shutdown()
print('screenshots em', OUT)
print('\n'.join(sorted(os.listdir(OUT))))
