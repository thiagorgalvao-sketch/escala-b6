# Separador de faixas (Modal + Supabase)

Serviço que separa um áudio em 6 faixas por instrumento (vocal, bateria,
baixo, guitarra, teclado, outros) usando Demucs, chamado pelo botão
"STEMS" do app.

- `fervor_separador_faixas.py` — roda no [Modal](https://modal.com). Faz o
  trabalho pesado (baixa o áudio, separa, sobe as 6 faixas no Storage do
  Supabase) e expõe duas rotas HTTP: `iniciar` e `status`.
- `edge-function.ts` — a função `separar-faixas` do Supabase. É só uma
  ponte fina: confere se quem chamou é administrador e repassa pro Modal
  (o plano gratuito do Supabase derruba funções que rodam mais de ~150s,
  por isso ela nunca espera o resultado — só pergunta "já terminou?").
- `15_faixas_separadas.sql` — cria a pasta no Storage e as permissões.
  Cole no SQL Editor do Supabase (só precisa rodar de novo se o arquivo
  mudar).

## Publicar uma correção no Modal

```
pip install modal
modal token set --token-id SEU_ID --token-secret SEU_SECRET --profile=SEU_PERFIL
cd servidor/separar-faixas
modal deploy fervor_separador_faixas.py
```

Usa os secrets `API_KEY` e `fervor-supabase` que já devem existir na conta
do Modal (veja o fim de `15_faixas_separadas.sql`). Como o nome do app e
das rotas não mudam, não precisa alterar nada no Supabase depois.

## Histórico

Em 02/11/2026 o deploy anterior passou a falhar com
`ImportError: TorchCodec is required for save_with_torchcodec` — o
Demucs tentava salvar o áudio separado com `torchaudio.save()`, que em
versões recentes do torchaudio passou a exigir o pacote `torchcodec`
(não instalado). A correção foi separar com a API do Demucs e gravar os
arquivos `.wav` com `soundfile` em vez de depender do `torchaudio.save`.
