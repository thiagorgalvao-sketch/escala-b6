# Como atualizar o Fervor

## Código-fonte
- O código do app fica em **`tools/src/*.html`** (30 módulos, em ordem de nome: estilos, página, núcleo, e um módulo por assunto).
- `tools/app.html` é **gerado** juntando os módulos (`python3 tools/montar.py`). Não edite o `app.html` direto: a próxima montagem apaga a mudança. Os testes avisam se ele estiver diferente dos módulos.
- Para criar um assunto novo, crie `tools/src/NN_nome.html` com o número na ordem desejada (o conteúdo é só colado, na ordem).

## Publicar (um comando só)
```
python3 tools/release.py "O que mudou"
```
Sobe o número da versão, monta, gera `index.html` / `admin/index.html` / `versao.json`, roda os testes (precisa dar "TUDO CERTO"), faz commit, sincroniza com o robô (`pull --rebase`), envia (com novas tentativas) e acompanha os testes e o deploy no GitHub.
Opções: `--sem-testes`, `--sem-numero`, `--so-montar` (não envia).

## Automático no GitHub
- `tests.yml`: roda todos os testes (inclui a varredura de todas as telas e a conferência dos módulos) a cada envio; abre um aviso (issue) se falhar.
- `no-ar.yml`: depois do envio, confere se `fervor.website/versao.json` mostra a versão nova; se não aparecer em 5 min, pede novo deploy (até 3 vezes) e abre um aviso se não resolver.
- `sync.yml`: a cada 6 h atualiza agendas e `pub.json`; usa fila única e `pull --rebase` para não brigar com envios manuais.

## Dados
- Ficam no Supabase (projeto hofrthndlstofytlapzk); scripts SQL em `servidor/`.
- Nos Ajustes, **Verificar dados** mostra pendências e corrige com um toque o que é automático.
