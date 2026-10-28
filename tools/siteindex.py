# Gera o index.html do site da banda a partir do app: python3 siteindex.py APP.html OUT/index.html
# - injeta o shim (dados vêm de pub.json, sem escrita)
# - links do PWA e noindex (o site não aparece em buscadores)
# - remove dados de importação/migração que a banda não usa (página mais leve)
import os,re,sys,json
here=os.path.dirname(os.path.abspath(__file__))
HEAD=('<meta name="robots" content="noindex,nofollow,noarchive"><meta name="referrer" content="no-referrer">'
      '<link rel="manifest" href="manifest.webmanifest"><link rel="apple-touch-icon" href="icon-180.png">'
      '<link rel="icon" type="image/svg+xml" href="favicon.svg"><link rel="icon" type="image/png" sizes="48x48" href="favicon-48.png">'
      '<meta property="og:type" content="website"><meta property="og:site_name" content="Fervor"><meta property="og:title" content="Fervor"><meta property="og:description" content="Escala, repertórios e devocionais da banda. “Sejam fervorosos no espírito, servindo ao Senhor.” (Romanos 12:11)"><meta property="og:url" content="https://fervor.website/"><meta property="og:image" content="https://fervor.website/og.png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:image:alt" content="Logo Fervor: letra F dentro de uma chama"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="https://fervor.website/og.png"><meta name="description" content="Escala, repertórios e devocionais da banda.">'
      '<meta name="apple-mobile-web-app-title" content="Escala B6">')
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
    m=re.search(r"const VER='([^']+)'",open(a,encoding='utf-8').read())
    if m: json.dump({'v':m.group(1)},open(os.path.join(os.path.dirname(os.path.abspath(o)),'versao.json'),'w'),ensure_ascii=False);print('versao',m.group(1))
