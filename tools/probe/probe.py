import urllib.request,urllib.parse,re,json,html
H1={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36','Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8','Accept-Language':'pt-BR,pt;q=0.9,en;q=0.8','Referer':'https://www.google.com/'}
def get(u,h=H1):
    try:
        r=urllib.request.urlopen(urllib.request.Request(u,headers=h),timeout=25);return r.status,r.read().decode('utf-8','replace')
    except Exception as e:
        b='';
        try:b=e.read().decode('utf-8','replace')[:120]
        except Exception:pass
        return getattr(e,'code',0),str(e)[:80]+' '+b
def note(m): print('::notice::'+m.replace('\n',' ')[:1500])
def info(t):
    m=re.search(r'<pre[^>]*>([\s\S]*?)</pre>',t)
    if not m: return 'sem pre'
    pre=html.unescape(re.sub(r'<[^>]+>','',m.group(1)));L=pre.split('\n')
    return f'pre_lines={len(L)} secoes={[x.strip() for x in L if re.match(r"^\s*\[[^\]]+\]",x)][:12]} tags={sorted(set(re.findall(r"<(\w+)",m.group(1))))}'
for u in ['https://www.cifraclub.com.br/nair-nany/melhor-amigo/','https://www.cifraclub.com.br/nair-nany/melhor-amigo/imprimir.html','https://m.cifraclub.com.br/nair-nany/melhor-amigo/','https://cifraclub.com.br/nair-nany/melhor-amigo/','https://www.cifras.com.br/cifra/nair-nany/melhor-amigo','https://www.letras.mus.br/nair-nany/melhor-amigo/']:
    st,t=get(u);note(f'{u} -> {st} len={len(t)} {info(t) if st==200 else t[:160]}')
st,t=get('https://www.cifraclub.com.br/nair-nany/melhor-amigo/',{'User-Agent':'curl/8.5.0','Accept':'*/*'})
note(f'curl-UA -> {st} {t[:120] if st!=200 else info(t)}')
