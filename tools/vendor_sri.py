# Gera vendor/manifest.json com versões e hashes (SRI) das bibliotecas hospedadas no site
import hashlib,base64,json,os
v=json.load(open('../tools/vendor.json'))
m={'versoes':v,'sri':{}}
for f in sorted(os.listdir('.')):
    if f.endswith(('.js','.mjs')):
        m['sri'][f]='sha384-'+base64.b64encode(hashlib.sha384(open(f,'rb').read()).digest()).decode()
json.dump(m,open('manifest.json','w'),indent=1)
print(json.dumps(m))
