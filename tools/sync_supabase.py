# Atualiza pub.json (cópia de segurança da visão da banda) e as agendas (.ics) a partir do Supabase.
# Roda no GitHub Actions: python3 tools/sync_supabase.py
import json,os,sys,tempfile,subprocess,urllib.request
SB='https://hofrthndlstofytlapzk.supabase.co/rest/v1/pub?select=id,j&order=id'
KEY='sb_publishable_Hmstttzx95SEN24Olsuk0g_AuPGnkX7'
req=urllib.request.Request(SB,headers={'apikey':KEY,'Accept':'application/json'})
rows=json.load(urllib.request.urlopen(req,timeout=60))
if not rows: sys.exit('Supabase sem dados em pub; nada alterado')
d=tempfile.mkdtemp()
for r in rows:
    json.dump({'j':r['j']},open(os.path.join(d,r['id']+'.json'),'w'),ensure_ascii=False)
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
subprocess.run([sys.executable,os.path.join(root,'tools','build.py'),'-',d,'',root],check=True)
print('pub',len(rows))
