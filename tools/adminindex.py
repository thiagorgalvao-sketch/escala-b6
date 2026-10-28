# Gera a página de administração (login pelo Supabase): python3 adminindex.py APP.html OUT/admin/index.html
import os,sys
here=os.path.dirname(os.path.abspath(__file__))
HEAD=('<meta name="robots" content="noindex,nofollow,noarchive"><meta name="referrer" content="no-referrer">'
      '<link rel="icon" type="image/png" href="../icon-192.png"><link rel="apple-touch-icon" href="../icon-180.png">'
      '<meta name="apple-mobile-web-app-title" content="B6 Admin">')
SB='<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/dist/umd/supabase.min.js"></script>'
def build(s):
    sh=open(os.path.join(here,'sbshim.js'),encoding='utf-8').read()
    i=s.find('<script');assert i>0
    s=s[:i]+SB+'\n<script>'+sh+'</script>\n'+s[i:]
    return s.replace('</head>',HEAD+'</head>',1)
if __name__=='__main__':
    a,o=sys.argv[1:3];os.makedirs(os.path.dirname(o),exist_ok=True)
    open(o,'w',encoding='utf-8').write(build(open(a,encoding='utf-8').read()))
    print('admin',os.path.getsize(o))
