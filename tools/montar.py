# Junta os módulos de tools/src/*.html (em ordem de nome) em tools/app.html.
# Uso: python3 tools/montar.py          -> escreve tools/app.html
#      python3 tools/montar.py --check  -> só confere se tools/app.html está igual aos módulos (usado nos testes)
import os, sys, glob
here = os.path.dirname(os.path.abspath(__file__))
def montar():
    fs = sorted(glob.glob(os.path.join(here, 'src', '*.html')))
    return ''.join(open(f, encoding='utf-8', newline='').read() for f in fs)
if __name__ == '__main__':
    out = os.path.join(here, 'app.html')
    s = montar()
    if '--check' in sys.argv:
        cur = open(out, encoding='utf-8', newline='').read() if os.path.exists(out) else ''
        if cur != s:
            print('tools/app.html está diferente dos módulos em tools/src — rode: python3 tools/montar.py'); sys.exit(1)
        print('app.html confere com os módulos'); sys.exit(0)
    open(out, 'w', encoding='utf-8', newline='').write(s)
    print('app.html montado:', len(s), 'bytes de', len(glob.glob(os.path.join(here, 'src', '*.html'))), 'módulos')
