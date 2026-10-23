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
HEAD='<link rel="manifest" href="manifest.webmanifest"><link rel="apple-touch-icon" href="icon-180.png"><link rel="icon" type="image/png" href="icon-192.png"><meta name="apple-mobile-web-app-title" content="Escala B6">'
s=s.replace('</head>',HEAD+'</head>',1)
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
# ===== agenda por pessoa (assinatura webcal)
import unicodedata,re as _re
def slug(n): return _re.sub(r'[^a-z0-9]+','-',unicodedata.normalize('NFD',n).encode('ascii','ignore').decode().lower()).strip('-')
RL={'vm':'Voz masculina','vf':'Voz feminina','so':'Soprano','co':'Contralto','te':'Tenor','bt':'Bateria','bx':'Baixo','tc':'Teclado','gt':'Guitarra','vi':'Violão'}
ADR={'maua':'Av. Cap. João, 1337 - Matriz, Mauá - SP, 09360-120','santo andre':'Av. Pedro Américo, 36 - Vila Humaita, Santo André - SP, 09110-560'}
def adr(p): k=unicodedata.normalize('NFD',p or '').encode('ascii','ignore').decode().lower().strip();return ADR.get(k,p or '')
SITE='https://thiagorgalvao-sketch.github.io/escala-b6/'
def esc(t): return str(t or '').replace('\\','\\\\').replace(';','\\;').replace(',','\\,').replace('\n','\\n')
def tt(d,h,add=0):
    a,b=map(int,h.split(':'));x=a*60+b+add;return d.replace('-','')+'T%02d%02d00'%((x//60)%24,x%60)
def nxt(d):
    x=datetime.date.fromisoformat(d)+datetime.timedelta(days=1);return x.strftime('%Y%m%d')
lim=(datetime.date.fromisoformat(today)-datetime.timedelta(days=45)).isoformat()
people={}
for k,l in lists.items():
    for r,n in (l.get('banda') or {}).items():
        n=(n or '').strip()
        if n and r in RL: people.setdefault(n,[]).append((l,r))
agd=os.path.join(OUT,'agenda');os.makedirs(agd,exist_ok=True)
for f in os.listdir(agd): os.remove(os.path.join(agd,f))
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
for n,L in people.items():
    ev=[]
    seen=set()
    for l,r in L:
        d=l.get('date') or ''
        if not d or d<lim or id(l) in seen: continue
        seen.add(id(l))
        roles=', '.join(RL[x] for x,v in (l.get('banda') or {}).items() if (v or '').strip()==n and x in RL)
        nm=' - '.join(x for x in [l.get('place'),l.get('turno')] if x)+(' · '+l['name'] if l.get('name') else '')
        sids=l.get('songIds') or []
        mus='\n'.join('- '+json.loads(D['s_'+i]['j']).get('title','') for i in sids if 's_'+i in D)
        desc='Você: '+roles+'\n'+('Banda pronta: '+l['hBanda']+'\n' if l.get('hBanda') else '')+('Repertório:\n'+mus if mus else 'Repertório a definir')+'\n\n'+SITE
        lid=l.get('id') or ''
        ok=lambda h:bool(_re.match(r'^\d{1,2}:\d{2}$',h or ''))
        def addm(h,m):
            a,b=map(int,h.split(':'));x=a*60+b+m;return '%02d:%02d'%((x//60)%24,x%60)
        st=l.get('hBanda') if ok(l.get('hBanda')) else (l.get('passHora') if ok(l.get('passHora')) else '')
        pl=unicodedata.normalize('NFD',l.get('place') or '').encode('ascii','ignore').decode().lower().strip();tu=(l.get('turno') or '').lower();nmv=(l.get('name') or '').lower()
        kk='dm' if pl=='santo andre' and 'domingo' in nmv and 'manh' in tu else ('dn' if pl=='santo andre' and 'domingo' in nmv and 'noite' in tu else '')
        hr=[x for x in [('Banda pronta: '+l['hBanda']) if l.get('hBanda') else '',('Gain / check de sinal: '+l['hGain']) if l.get('hGain') else '',('Início da passagem: '+l['passHora']) if l.get('passHora') else '',('Término da passagem: '+l['passFim']) if l.get('passFim') else ''] if x]
        desc='Você: '+roles+'\n\n'+(('HORÁRIOS\n'+'\n'.join(hr)+'\n\n') if hr else '')+('REPERTÓRIO\n'+mus if mus else 'Repertório a definir')+'\n\n'+SITE
        if st:
            en='11:30' if kk=='dm' else ('20:30' if kk=='dn' else addm(l['passFim'] if ok(l.get('passFim')) else addm(st,40),150))
            if en<=st: en=addm(st,180)
            ev.append(('culto-'+lid,'Culto · '+nm,'DTSTART;TZID=America/Sao_Paulo:'+tt(d,st),'DTEND;TZID=America/Sao_Paulo:'+tt(d,en),adr(l.get('place')),desc))
        else:
            ev.append(('culto-'+lid,'Culto · '+nm,'DTSTART;VALUE=DATE:'+d.replace('-',''),'DTEND;VALUE=DATE:'+nxt(d),adr(l.get('place')),desc))
        ed=l.get('ensData') or '';eh=l.get('ensHora') or ''
        if ed and not l.get('semEns'):
            if _re.match(r'^\d{1,2}:\d{2}$',eh): ev.append(('ens-'+lid,'Ensaio · '+nm,'DTSTART;TZID=America/Sao_Paulo:'+tt(ed,eh),'DTEND;TZID=America/Sao_Paulo:'+tt(ed,eh,120),l.get('ensLocal') or l.get('place') or '',desc))
            else: ev.append(('ens-'+lid,'Ensaio · '+nm,'DTSTART;VALUE=DATE:'+ed.replace('-',''),'DTEND;VALUE=DATE:'+nxt(ed),l.get('ensLocal') or l.get('place') or '',desc))
    o=['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//Escala B6//PT-BR','CALSCALE:GREGORIAN','METHOD:PUBLISH','X-WR-CALNAME:Escala B6 · '+n.split(' ')[0],'X-WR-TIMEZONE:America/Sao_Paulo','REFRESH-INTERVAL;VALUE=DURATION:PT6H','X-PUBLISHED-TTL:PT6H',
       'BEGIN:VTIMEZONE','TZID:America/Sao_Paulo','BEGIN:STANDARD','DTSTART:19700101T000000','TZOFFSETFROM:-0300','TZOFFSETTO:-0300','TZNAME:-03','END:STANDARD','END:VTIMEZONE']
    for u,t,a,b,loc,ds in ev: o+=['BEGIN:VEVENT','UID:'+u+'@escala-b6','DTSTAMP:'+stamp,a,b,'SUMMARY:'+esc(t),'LOCATION:'+esc(loc),'DESCRIPTION:'+esc(ds),'BEGIN:VALARM','ACTION:DISPLAY','DESCRIPTION:'+esc(t),'TRIGGER:-PT1H','END:VALARM','END:VEVENT']
    o.append('END:VCALENDAR')
    open(os.path.join(agd,slug(n)+'.ics'),'w',encoding='utf-8',newline='').write('\r\n'.join(o)+'\r\n')
print('agendas',len(people))
print('ok cultos',len(lists),'musicas',len(songs),'futuros sem publicar',sum(1 for k,l in lists.items() if k not in P and (l.get('date') or '')>=today))
