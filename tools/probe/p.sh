n(){ echo "::notice::$1" ; }
SB=https://hofrthndlstofytlapzk.supabase.co
K=sb_publishable_Hmstttzx95SEN24Olsuk0g_AuPGnkX7
r=$(curl -s -o /tmp/o -w "%{http_code}" -X POST "$SB/functions/v1/buscar-cifra" -H "apikey: $K" -H "Authorization: Bearer $K" -H "content-type: application/json" -d '{"acao":"buscar","q":"tudo e perda"}'); n "FN buscar-cifra $r $(head -c 200 /tmp/o)"
r=$(curl -s -o /tmp/o -w "%{http_code}" -X OPTIONS "$SB/functions/v1/buscar-cifra" -H "Origin: https://fervor.website" -H "Access-Control-Request-Method: POST" -H "Access-Control-Request-Headers: authorization,apikey,content-type,x-client-info"); n "FN OPTIONS $r $(head -c 100 /tmp/o)"
h=$(curl -s -D - -o /dev/null "https://www.youtube.com/oembed?format=json&url=https%3A%2F%2Fyoutu.be%2FdQw4w9WgXcQ" -H "Origin: https://fervor.website" | grep -i "^HTTP\|access-control" | tr '\r\n' '  '); n "YT oembed $h"
h=$(curl -s -D - -o /tmp/o "https://noembed.com/embed?url=https%3A%2F%2Fyoutu.be%2FdQw4w9WgXcQ" -H "Origin: https://fervor.website" | grep -i "^HTTP\|access-control" | tr '\r\n' '  '); n "noembed $h $(head -c 120 /tmp/o)"
U=https://www.cifraclub.com.br/nair-nany/melhor-amigo/
for P in "https://r.jina.ai/$U" "https://api.allorigins.win/raw?url=$U" "https://corsproxy.io/?url=$U" "https://api.codetabs.com/v1/proxy?quest=$U" "https://www.cifraclub.com.br/nair-nany/melhor-amigo/imprimir.html" "https://www.cifras.com.br/cifra/nair-nany/melhor-amigo" "https://m.cifraclub.com.br/nair-nany/melhor-amigo/" "https://www.cifraclub.com.br/nair-nany/melhor-amigo/?fv=1" "https://webcache.googleusercontent.com/search?q=cache:$U"; do
 r=$(curl -s -L -m 25 -o /tmp/o -w "%{http_code}" "$P" -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36" -H "Accept-Language: pt-BR" -H "Origin: https://fervor.website" -D /tmp/h); c=$(grep -ci "access-control-allow-origin" /tmp/h); pre=$(grep -c "<pre\|\[Intro\]\|\[Refrão\]\|Primeira Parte" /tmp/o); n "PX $P => $r cors=$c pre=$pre size=$(wc -c </tmp/o) $(grep -o 'Primeira Parte[^<]\{0,60\}\|\[Intro\][^<]\{0,60\}' /tmp/o | head -1)"
done
