import json,os,sys
APP,PUB,OUT=sys.argv[1:4]
s=open(APP,encoding='utf-8').read();sh=open(os.path.join(os.path.dirname(__file__),'shim.js')).read()
i=s.find('<script');assert i>0
s=s[:i]+'<script>'+sh+'</script>\n'+s[i:]
os.makedirs(OUT,exist_ok=True);open(os.path.join(OUT,'index.html'),'w',encoding='utf-8').write(s)
P={}
for f in os.listdir(PUB):
    if f.endswith('.json'):
        d=json.load(open(os.path.join(PUB,f)));P[f[:-5]]={'j':d['j'],'u':d.get('u')}
json.dump(P,open(os.path.join(OUT,'pub.json'),'w'),ensure_ascii=False)
print('ok',len(P))
