# Atualiza pub.json (cópia de segurança da visão da banda) e as agendas (.ics) a partir do Supabase.
# Roda no GitHub Actions: python3 tools/sync_supabase.py
import json,os,sys,tempfile,subprocess,urllib.request
SB='https://hofrthndlstofytlapzk.supabase.co/rest/v1/pub?select=id,j&order=id'
KEY='sb_publishable_Hmstttzx95SEN24Olsuk0g_AuPGnkX7'
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Com "Acesso somente com login e senha" ligado, a cópia pública (pub.json) e as agendas ficam vazias.
try:
    cfg=json.load(urllib.request.urlopen(urllib.request.Request(SB.split('/rest/v1/')[0]+'/rest/v1/config?select=chave,valor&chave=eq.login_banda',headers={'apikey':KEY,'Accept':'application/json'}),timeout=30))
except Exception: cfg=[]
if any(c.get('chave')=='login_banda' and c.get('valor') is True for c in cfg):
    json.dump({},open(os.path.join(root,'pub.json'),'w'))
    ag=os.path.join(root,'agenda')
    if os.path.isdir(ag):
        for f in os.listdir(ag): os.remove(os.path.join(ag,f))
    print('login obrigatório: cópia pública e agendas esvaziadas');sys.exit(0)
req=urllib.request.Request(SB,headers={'apikey':KEY,'Accept':'application/json'})
rows=json.load(urllib.request.urlopen(req,timeout=60))
if not rows: sys.exit('Supabase sem dados em pub; nada alterado')
d=tempfile.mkdtemp()
for r in rows:
    json.dump({'j':r['j']},open(os.path.join(d,r['id']+'.json'),'w'),ensure_ascii=False)
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
subprocess.run([sys.executable,os.path.join(root,'tools','build.py'),'-',d,'',root],check=True)
print('pub',len(rows))
