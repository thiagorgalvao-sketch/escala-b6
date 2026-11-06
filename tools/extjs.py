# Tira o script principal (o maior bloco <script>...</script>) da página e o grava em arquivo próprio.
# Vantagem: a página fica pequena e o app (com ?v=versão) fica guardado no aparelho; só baixa de novo quando a versão muda.
import re,os
def externalize(html,jsname,ver):
    blocos=[(m.start(),m.end(),m.group(1)) for m in re.finditer(r'<script>([\s\S]*?)</script>',html)]
    a,b,js=max(blocos,key=lambda x:len(x[2]))
    v=re.sub(r'\D','',ver.split('·')[-1]) if ver else '0'
    return html[:a]+'<script src="'+jsname+'?v='+v+'"></script>'+html[b:],js
