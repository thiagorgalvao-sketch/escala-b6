#!/usr/bin/env python3
# Publica uma versão nova do Fervor com um comando só.
# Uso:  python3 tools/release.py "O que mudou"            (sobe o número da versão, monta, testa, envia)
#       python3 tools/release.py "texto" --sem-testes     (pula os testes — só em emergência)
#       python3 tools/release.py "texto" --sem-numero     (não mexe no número da versão)
#       python3 tools/release.py "texto" --so-montar      (monta e testa, mas não faz commit/push)
# Passos: sobe VER nos módulos -> junta tools/src em tools/app.html -> gera index.html, admin/index.html e versao.json
#         -> roda os testes -> commit -> sincroniza com o robô (pull --rebase) -> push (com novas tentativas)
#         -> acompanha os testes e o deploy no GitHub (se o comando `gh` existir).
import os, re, sys, glob, json, time, subprocess, datetime
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(ROOT)
PY = sys.executable
TRAILER = os.environ.get('RELEASE_TRAILER', '')

def sh(*a, check=True, **k):
    r = subprocess.run(a, text=True, capture_output=True, **k)
    if check and r.returncode:
        print('✘', ' '.join(a), '\n', (r.stdout + r.stderr)[-1500:]); sys.exit(1)
    return r

def bump():
    fs = glob.glob('tools/src/*.html')
    for f in fs:
        s = open(f, encoding='utf-8', newline='').read()
        m = re.search(r"const VER='(\d\d/\d\d/\d{4}) · (\d+)'", s)
        if m:
            hoje = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=3)).strftime('%d/%m/%Y')
            novo = f"const VER='{hoje} · {int(m.group(2)) + 1}'"
            open(f, 'w', encoding='utf-8', newline='').write(s.replace(m.group(0), novo, 1))
            print('versão:', novo[11:-1]); return
    sys.exit('não achei const VER nos módulos')

def main():
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    flags = {x for x in sys.argv[1:] if x.startswith('--')}
    if not a and '--so-montar' not in flags:
        sys.exit(__doc__)
    msg = a[0] if a else 'montagem'
    if '--sem-numero' not in flags: bump()
    print(sh(PY, 'tools/montar.py').stdout.strip())
    sh(PY, 'tools/siteindex.py', 'tools/app.html', 'index.html')
    sh(PY, 'tools/adminindex.py', 'tools/app.html', 'admin/index.html')
    if '--sem-testes' not in flags:
        print('rodando testes (1–2 min)…')
        r = subprocess.run([PY, 'tools/tests/run.py'], text=True, capture_output=True)
        linhas = [l for l in r.stdout.splitlines() if l.startswith('✘') or 'TUDO CERTO' in l or 'FALHA' in l]
        print('\n'.join(linhas) or r.stdout[-800:])
        if r.returncode: sys.exit('✘ testes falharam — nada foi enviado')
    if '--so-montar' in flags: return
    ver = json.load(open('versao.json'))['v']
    sh('git', 'add', '-A', 'tools', 'index.html', 'admin', 'versao.json', '.github', 'sw.js', 'servidor')
    if sh('git', 'diff', '--cached', '--quiet', check=False).returncode == 0:
        sys.exit('nada para publicar')
    corpo = f'{msg} (VER {ver.split(" · ")[-1]})' if '--sem-numero' not in flags else msg
    sh('git', 'commit', '-m', corpo + ('\n\n' + TRAILER if TRAILER else ''))
    for i in range(1, 6):   # o robô de sincronização também publica: reaplica por cima e tenta de novo
        sh('git', 'pull', '--rebase', '--autostash', 'origin', 'main')
        r = sh('git', 'push', 'origin', 'HEAD:main', check=False)
        if r.returncode == 0: break
        print('push recusado, tentativa', i); time.sleep(3 * i)
    else: sys.exit('✘ não consegui enviar depois de 5 tentativas')
    print('✔ enviado:', ver)
    if subprocess.run(['which', 'gh'], capture_output=True).returncode: return
    sha = sh('git', 'rev-parse', 'HEAD').stdout.strip()
    ate = time.time() + 600; vistos = {}
    while time.time() < ate:
        r = sh('gh', 'run', 'list', '--commit', sha, '--json', 'name,status,conclusion', check=False)
        try: runs = json.loads(r.stdout or '[]')
        except Exception: runs = []
        for x in runs: vistos[x['name']] = (x['status'], x['conclusion'])
        print('  ', {k: (v[1] or v[0]) for k, v in vistos.items()})
        if vistos and all(v[0] == 'completed' for v in vistos.values()) and any('Testes' in k for k in vistos): break
        time.sleep(30)
    bad = {k: v for k, v in vistos.items() if v[0] == 'completed' and v[1] not in ('success', 'skipped')}
    if bad: sys.exit(f'✘ falhou no GitHub: {bad}')
    print('✔ testes e deploy do GitHub concluídos (o workflow "no ar" confere o site e pede novo deploy se travar)')

main()
