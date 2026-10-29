U=https://www.cifraclub.com.br/nair-nany/melhor-amigo/
mkdir -p out
curl -s -D out/solr.h "https://solr.sscdn.co/cc/c7/?q=melhor%20amigo" -H "Origin: https://fervor.website" -o out/solr.json
curl -s -m 40 "https://r.jina.ai/$U" -o out/j1.txt -D out/j1.h
curl -s -m 40 "https://r.jina.ai/$U" -H "X-Return-Format: html" -o out/j2.html
curl -s -m 40 "https://r.jina.ai/$U" -H "X-Target-Selector: pre" -o out/j3.txt
curl -s -m 40 "https://r.jina.ai/$U" -H "X-Return-Format: text" -H "X-Target-Selector: .cifra_cnt" -o out/j4.txt
curl -s -m 40 "https://r.jina.ai/https://www.cifraclub.com.br/aline-barros/ressuscita-me/" -H "X-Return-Format: html" -H "X-Target-Selector: pre" -o out/j5.html
curl -s -m 40 "https://r.jina.ai/https://www.cifraclub.com.br/nair-nany/melhor-amigo/imprimir.html" -o out/j6.txt
