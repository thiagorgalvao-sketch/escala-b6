# Sonda temporária: verifica formatos de busca/página de cifra (não grava conteúdo, só estrutura)
import urllib.request,urllib.parse,re,json,html
UA={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36','Accept-Language':'pt-BR,pt;q=0.9'}
def get(u):
    try:
        r=urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=25);return r.status,r.read().decode('utf-8','replace')
    except Exception as e: return getattr(e,'code',0),str(e)
def note(m): print('::notice::'+m.replace('\n',' ')[:1800])
q='melhor amigo nair nany'
for u in ['https://solr.sscdn.co/cc/h2/?q='+urllib.parse.quote(q),'https://solr.sscdn.co/cc/c7/?q='+urllib.parse.quote(q)]:
    st,t=get(u);note(f'SOLR {u[-40:]} status={st} len={len(t)} head={t[:700]}')
st,t=get('https://www.cifraclub.com.br/nair-nany/melhor-amigo/')
note(f'PAGE status={st} len={len(t)} pre={len(re.findall(r"<pre",t))} cifra_tom={"cifra_tom" in t} h1={re.findall(r"<h1[^>]*>(.*?)</h1>",t)[:2]} h2={[re.sub("<[^>]+>","",x)[:60] for x in re.findall(r"<h2[^>]*>(.*?)</h2>",t,re.S)[:2]]}')
m=re.search(r'<pre[^>]*>([\s\S]*?)</pre>',t)
if m:
    pre=html.unescape(re.sub(r'<[^>]+>','',m.group(1)));L=pre.split('\n')
    secs=[x.strip() for x in L if re.match(r'^\s*\[[^\]]+\]',x)]
    note(f'PRE lines={len(L)} secoes={secs[:20]} tags={sorted(set(re.findall(r"<(\w+)",m.group(1))))} tom_ctx={re.sub(r"<[^>]+>"," ",t[t.find("cifra_tom"):t.find("cifra_tom")+300])[:200] if "cifra_tom" in t else ""}')
    note('PRE_CHORDS '+' | '.join(x for x in L if x.strip() and re.fullmatch(r'[\sA-G#b/m0-9()+°ºMadijsu\-|]+',x))[:600])
st,t=get('https://html.duckduckgo.com/html/?q='+urllib.parse.quote('cifraclub '+q))
links=re.findall(r'cifraclub\.com\.br/([a-z0-9\-]+)/([a-z0-9\-]+)/',html.unescape(urllib.parse.unquote(t)))
note(f'DDG status={st} len={len(t)} links={links[:6]}')
st,t=get('https://www.cifraclub.com.br/?q='+urllib.parse.quote(q))
note(f'CCSEARCH status={st} len={len(t)} links={re.findall(r"href=\"/([a-z0-9-]+)/([a-z0-9-]+)/\"",t)[:6]} gcse={"cse" in t}')
