# Gera o site da banda: python3 build.py APP.html PUB_DIR TEAM_DIR OUT_DIR [ASSETS_DIR]
# Audios enviados ao app (/_blob/...) viram OUT_DIR/media/<id>.mp3. Se faltar o arquivo,
# o script lista os ids em 'faltando:' (baixe cada um com Artifact read path=<id> para ASSETS_DIR e rode de novo).
# Inclui todos os cultos: passados (com repertorio), proximos publicados (como publicados)
# e proximos ainda nao publicados (so a escala, sem musicas).
import json,os,sys,datetime,glob,subprocess,tempfile
APP,PUB,TEAM,OUT=sys.argv[1:5]
ASSETS=sys.argv[5] if len(sys.argv)>5 else ''
MISSING=set()
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
def asset(i):
    for f in glob.glob(os.path.join(ASSETS,i+'*')) if ASSETS else []: return f
    return None
def media(u):
    """/_blob/x ou ck:/_blob/a|/_blob/b -> media/<id>.mp3 (ou None)"""
    ck=u.startswith('ck:');ids=[x.split('/_blob/')[1] for x in (u[3:] if ck else u).split('|') if '/_blob/' in x]
    if not ids: return None
    rel='media/'+ids[0]+'.mp3';dst=os.path.join(OUT,rel)
    if os.path.exists(dst): return rel
    fs=[asset(i) for i in ids]
    if not all(fs): MISSING.update(i for i,f in zip(ids,fs) if not f);return None
    os.makedirs(os.path.dirname(dst),exist_ok=True)
    with tempfile.NamedTemporaryFile(delete=False) as t:
        for f in fs:
            b=open(f,'rb').read();t.write(b[4:] if ck else b)
    r=subprocess.run(['ffmpeg','-y','-loglevel','error','-i',t.name,'-vn','-ac','2','-b:a','160k',dst]);os.unlink(t.name)
    return rel if r.returncode==0 and os.path.exists(dst) else None
def fix(v):
    if isinstance(v,dict) and '_blob' in str(v.get('url','')):
        r=media(v['url'])
        if not r: return None
        v=dict(v);v['url']=r;v.pop('id',None);v['name']=os.path.splitext(v.get('name') or 'audio')[0]+'.mp3';v.pop('size',None);return v
    return v
def noblob(o):
    for k in ['ba','vs']:
        if k in o:
            v=fix(o[k])
            if v is None: del o[k]
            else: o[k]=v
    if 'bas' in o:
        o['bas']=[v for v in (fix(x) for x in o['bas']) if v]
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
if MISSING: print('faltando:',' '.join(sorted(MISSING)))
print('ok cultos',len(lists),'musicas',len(songs),'futuros sem publicar',sum(1 for k,l in lists.items() if k not in P and (l.get('date') or '')>=today))
