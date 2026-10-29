import urllib.request,urllib.parse,re,json,html
H1={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36','Accept':'text/html,*/*','Accept-Language':'pt-BR,pt;q=0.9'}
def get(u):
    try:
        r=urllib.request.urlopen(urllib.request.Request(u,headers=H1),timeout=25);return r.status,r.read().decode('utf-8','replace')
    except Exception as e: return getattr(e,'code',0),str(e)[:80]
def note(m): print('::notice::'+m.replace('\n','⏎')[:1800])
st,t=get('https://www.cifras.com.br/cifra/nair-nany/melhor-amigo')
i=t.find('<pre');note('PRE_CTX '+re.sub(r'[A-Za-zÀ-ú]{3,}','w',t[i-400:i+900]))
note('TAGS '+str(sorted(set(re.findall(r'<pre[^>]*>',t)))[:300])+' tom='+str(re.findall(r'(?i)tom[^<]{0,20}<[^>]*>([A-G][#b]?m?)<',t)[:3]))
note('H1 '+str([re.sub('<[^>]+>','',x)[:60] for x in re.findall(r'<h1[^>]*>([\s\S]*?)</h1>',t)][:2])+' H2 '+str([re.sub('<[^>]+>','',x).strip()[:60] for x in re.findall(r'<h2[^>]*>([\s\S]*?)</h2>',t)][:3]))
note('JSONLD '+str([x[:200] for x in re.findall(r'<script type="application/ld\+json">([\s\S]*?)</script>',t)][:2]))
st,t=get('https://www.cifras.com.br/busca?q='+urllib.parse.quote('melhor amigo nair nany'))
note(f'BUSCA {st} len={len(t)} links={re.findall(r"href=\"(?:https://www.cifras.com.br)?/cifra/([a-z0-9-]+)/([a-z0-9-]+)\"",t)[:6]}')
st,t=get('https://html.duckduckgo.com/html/?q='+urllib.parse.quote('cifras.com.br melhor amigo nair nany'))
note('DDG cifras.com.br '+str(re.findall(r'cifras\.com\.br/cifra/([a-z0-9\-]+)/([a-z0-9\-]+)',urllib.parse.unquote(t))[:5]))
