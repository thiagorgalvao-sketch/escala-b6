# Declaração de autoria

**Sistema:** Fervor (repositório `escala-b6`) — plataforma de escala e repertório para bandas de louvor, com separação de faixas por IA (stems), mixer de ensaio, detecção de tom e sincronização offline-first.

**Autor:** Thiago Rodrigo Galvão

**E-mail de contato:** thiagorgalvao@gmail.com

**Identificação do autor (CPF), sem expor o número publicamente:**
Hash SHA-256 de `"Thiago Rodrigo Galvão|<CPF formatado com pontos e traço>|2026-10-31"` (campos separados por `|`, data no formato `AAAA-MM-DD`):

```
f4c850870c0f764f3bda432eec59d716a3992a43d6bce5fab09e29ecbe16b87c
```

Esse hash não revela o CPF hoje. Serve para, se um dia for necessário, o autor revelar o número exato e qualquer pessoa recalcular o hash acima com a fórmula descrita e confirmar que esse CPF já era conhecido nesta data — sem precisar publicá-lo agora.

**Data desta declaração:** 31/10/2026

**Estado do repositório no momento desta declaração:** commit `2eda165b134261dd6e0e97eb32e6dadab712c909` (branch `main`, repositório `thiagorgalvao-sketch/escala-b6`).

**Declaro que** sou o autor e detentor dos direitos do código-fonte, da concepção e do desenvolvimento deste sistema, cuja autoria nasce automaticamente no momento da criação (Lei nº 9.609/1998 — Lei do Software, e Lei nº 9.610/1998 — Lei de Direitos Autorais). Este documento, o histórico de commits deste repositório (com timestamps registrados pelo próprio GitHub) e a assinatura GPG abaixo têm como único propósito reforçar a prova de autoria e de anterioridade, sem prejuízo da proteção legal já existente de forma automática.

## Verificação por assinatura GPG

Este documento (`AUTORIA.md`, no estado em que foi comitado) é selado por uma assinatura digital destacada, usando a chave pública abaixo.

- **Chave pública:** arquivo [`pubkey.asc`](./pubkey.asc), também publicada nos servidores de chaves públicos de OpenPGP.
- **Fingerprint:** `4DB5 1F5B 6E92 5BD9 BFE0 573B FE01 B1AD DB69 CB2A`
- **Assinatura destacada:** arquivo [`AUTORIA.md.asc`](./AUTORIA.md.asc)

Para verificar (depois de importar `pubkey.asc` com `gpg --import pubkey.asc`):

```
gpg --verify AUTORIA.md.asc AUTORIA.md
```

## Reforço opcional: selo de tempo na blockchain (OpenTimestamps)

Além da assinatura acima e do histórico do GitHub (que já registra a data deste commit em um servidor independente), é possível ancorar este arquivo na blockchain do Bitcoin de forma gratuita, usando o [OpenTimestamps](https://opentimestamps.org/). Isso cria uma prova adicional de que este conteúdo exato existia nesta data, verificável para sempre, mesmo que o GitHub ou este repositório deixem de existir.

Para gerar esse selo (rodando no seu computador, com Python instalado):

```
pip install opentimestamps-client
ots stamp AUTORIA.md
```

Isso cria o arquivo `AUTORIA.md.ots`. Guarde-o e, se quiser, adicione-o a este repositório. Depois de algumas horas (quando a prova for confirmada na blockchain), rode `ots upgrade AUTORIA.md.ots` e depois `ots verify AUTORIA.md.ots` para confirmar.
