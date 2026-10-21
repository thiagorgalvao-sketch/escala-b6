# Gera o site da banda: python3 build.py APP.html PUB_DIR TEAM_DIR OUT_DIR
# Inclui todos os cultos: passados (com repertorio), proximos publicados (como publicados)
# e proximos ainda nao publicados (so a escala, sem musicas).
import json,os,sys,datetime
APP,PUB,TEAM,OUT=sys.argv[1:5]
here=os.path.dirname(os.path.abspath(__file__))
s=open(APP,encoding='utf-8').read();sh=open(os.path.join(here,'shim.js')).read()
i=s.find('<script');assert i>0
s=s[:i]+'<script>'+sh+'</script>\n'+s[i:]
def load(d):
    o={}
    for f in os.listdir(d) if d and os.path.isdir(d) else []:
        if f.endswith('.json'):
            try: o[f[:-5]]=json.loads(json.load(open(os.path.join(d,f)))['j'])
            except Exception: pass
    return o
P,T=load(PUB),load(TEAM)
today=(datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(hours=3)).strftime('%Y-%m-%d')
def noblob(o):
    for k in ['ba','vs']:
        if k in o and '_blob' in json.dumps(o[k]): del o[k]
    if 'bas' in o:
        o['bas']=[x for x in o['bas'] if '_blob' not in json.dumps(x)]
        if not o['bas']: del o['bas']
    if 'files' in o and '_blob' in json.dumps(o['files']): del o['files']
    o.pop('hist',None);return o
lists={}
for k in set(x for x in list(T)+list(P) if x.startswith('l_')):
    if k in P: l=P[k]
    else:
        l=dict(T[k])
        if (l.get('date') or '')>=today:
            for f in ['songIds','keys','cant','ord','rot','rn','tr','slot','nota','files']: l.pop(f,None)
            l['songIds']=[]
    lists[k]=noblob(l)
need=set(i for l in lists.values() for i in (l.get('songIds') or []))
songs={}
for i in need:
    k='s_'+i;o=P.get(k) or T.get(k)
    if o: songs[k]=noblob(dict(o))
os.makedirs(OUT,exist_ok=True)
open(os.path.join(OUT,'index.html'),'w',encoding='utf-8').write(s)
D={k:{'j':json.dumps(v,ensure_ascii=False)} for k,v in {**lists,**songs}.items()}
json.dump(D,open(os.path.join(OUT,'pub.json'),'w'),ensure_ascii=False,separators=(',',':'))
print('ok cultos',len(lists),'musicas',len(songs),'futuros sem publicar',sum(1 for k,l in lists.items() if k not in P and (l.get('date') or '')>=today))
