n(){ echo "::notice::$1" ; }
h=$(curl -s -D - -o /dev/null -X OPTIONS "https://r.jina.ai/https://www.cifraclub.com.br/nair-nany/melhor-amigo/" -H "Origin: https://fervor.website" -H "Access-Control-Request-Method: GET" -H "Access-Control-Request-Headers: x-return-format,x-target-selector" | tr '\r\n' '  '); n "JINA OPT $h"
h=$(curl -s -D - -o /tmp/o "https://open.spotify.com/oembed?url=https://open.spotify.com/track/4cOdK2wGLETKBW3PvgPWqT" -H "Origin: https://fervor.website" | grep -i "^HTTP\|access-control" | tr '\r\n' '  '); n "SPOT $h $(head -c 300 /tmp/o)"
