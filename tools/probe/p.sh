mkdir -p out
t0=$(date +%s%N)
curl -s -m 40 "https://r.jina.ai/https://www.cifraclub.com.br/nair-nany/melhor-amigo/" -H "X-Return-Format: html" -H "X-Target-Selector: h1,[data-chord-config],pre" -o out/k1.html -D out/k1.h
echo "ms $(( ($(date +%s%N)-t0)/1000000 ))" > out/time.txt
curl -s -m 40 "https://r.jina.ai/https://www.cifraclub.com.br/fernandinho/uma-nova-historia/" -H "X-Return-Format: html" -H "X-Target-Selector: h1,[data-chord-config],pre" -o out/k2.html
curl -s -m 40 "https://r.jina.ai/https://www.cifraclub.com.br/fernandinho/nao-existe/" -H "X-Return-Format: html" -H "X-Target-Selector: h1,[data-chord-config],pre" -o out/k3.html -D out/k3.h
curl -s "https://solr.sscdn.co/cc/c7/?q=fernandinho%20uma%20nova%20historia" -o out/s2.json
