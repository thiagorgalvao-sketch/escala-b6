# Gera o index.html do site da banda a partir do app: python3 siteindex.py APP.html OUT/index.html
# - injeta o shim (dados vêm de pub.json, sem escrita)
# - links do PWA e noindex (o site não aparece em buscadores)
# - remove dados de importação/migração que a banda não usa (página mais leve)
import os,re,sys
here=os.path.dirname(os.path.abspath(__file__))
HEAD=('<meta name="robots" content="noindex,nofollow,noarchive"><meta name="referrer" content="no-referrer">'
      '<link rel="manifest" href="manifest.webmanifest"><link rel="apple-touch-icon" href="icon-180.png">'
      '<link rel="icon" type="image/png" href="icon-192.png"><meta name="apple-mobile-web-app-title" content="Escala B6">')
STRIP={'SEED':'[]','EV2':'[]','PD':'[]','VMIMP':'{}'}
def build(s):
    for k,v in STRIP.items():
        s,n=re.subn(r'(?m)^const '+k+r'=.*;[ \t]*$', 'const '+k+'='+v+';', s, count=1)
    sh=open(os.path.join(here,'shim.js'),encoding='utf-8').read()
    i=s.find('<script');assert i>0
    s=s[:i]+'<script>'+sh+'</script>\n'+s[i:]
    return s.replace('</head>',HEAD+'</head>',1)
if __name__=='__main__':
    a,o=sys.argv[1:3]
    open(o,'w',encoding='utf-8').write(build(open(a,encoding='utf-8').read()))
    print('index',os.path.getsize(o))
