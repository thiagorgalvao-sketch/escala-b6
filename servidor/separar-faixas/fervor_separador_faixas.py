# Fervor · Separador de faixas (Modal)
#
# Recebe o link de um áudio, separa em 6 faixas por instrumento (vocal, bateria,
# baixo, guitarra, teclado, outros) com o Demucs (modelo htdemucs_6s), sobe cada
# faixa pronta no Storage do Supabase (bucket "faixas-separadas") e devolve os
# links públicos. Pensado para ser chamado pela Edge Function "separar-faixas"
# do Supabase, que só repassa duas ações:
#   POST .../iniciar  {chave, url, musica_id} -> {call_id}
#   POST .../status   {chave, call_id}        -> {status:"processando"}
#                                                 {status:"pronto", faixas:{...}}
#                                                 {status:"erro", erro:"..."}
#
# Correção importante nesta versão: o Demucs, por padrão, salva o áudio
# separado usando torchaudio.save(), que em versões recentes do torchaudio
# passou a exigir o pacote "torchcodec" (não incluído aqui de propósito).
# Em vez de depender disso, esta versão separa com a API do Demucs e grava
# os arquivos .wav sozinha, com a biblioteca "soundfile" — mais simples,
# mais estável, sem essa dependência frágil.
#
# Deploy: modal deploy fervor_separador_faixas.py
# (usa os secrets "fervor-api-key" e "fervor-supabase" que já devem existir no Modal —
#  veja 15_faixas_separadas.sql no projeto para como criá-los, se precisar.)

import os
import uuid

import modal

app = modal.App("fervor-separador-faixas")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("ffmpeg")
    .pip_install(
        "torch==2.3.1",
        "torchaudio==2.3.1",
        "demucs==4.0.1",
        "soundfile==0.12.1",
        "httpx==0.27.2",
        "fastapi[standard]",
        "numpy<2",
    )
)

SECRETS = [modal.Secret.from_name("fervor-api-key"), modal.Secret.from_name("fervor-supabase")]

# nome do stem no Demucs (htdemucs_6s) -> nome em português usado pelo app
STEM_PT = {
    "vocals": "vocal",
    "drums": "bateria",
    "bass": "baixo",
    "guitar": "guitarra",
    "piano": "teclado",
    "other": "outros",
}


def _checar_chave(chave: str):
    esperado = ""
    for nome in ("API_KEY", "MODAL_API_KEY", "FERVOR_API_KEY", "CHAVE"):
        esperado = os.environ.get(nome, "")
        if esperado:
            break
    if not esperado or chave != esperado:
        raise PermissionError("chave inválida")


@app.function(image=image, secrets=SECRETS, gpu="T4", timeout=900, memory=8192)
def separar(url: str, musica_id: str) -> dict:
    import httpx
    import soundfile as sf
    import torch
    from demucs.apply import apply_model
    from demucs.audio import AudioFile, convert_audio
    from demucs.pretrained import get_model

    tmp = f"/tmp/{uuid.uuid4().hex}"
    os.makedirs(tmp, exist_ok=True)
    origem = f"{tmp}/origem"

    # 1) baixa o áudio de referência
    with httpx.Client(follow_redirects=True, timeout=120) as c:
        r = c.get(url)
        r.raise_for_status()
        with open(origem, "wb") as f:
            f.write(r.content)

    # 2) separa com o Demucs (6 faixas)
    modelo = get_model("htdemucs_6s")
    modelo.cpu() if not torch.cuda.is_available() else modelo.cuda()
    modelo.eval()
    dispositivo = "cuda" if torch.cuda.is_available() else "cpu"

    wav = AudioFile(origem).read(streams=0, samplerate=modelo.samplerate, channels=modelo.audio_channels)
    wav = convert_audio(wav, modelo.samplerate, modelo.samplerate, modelo.audio_channels)
    ref = wav.mean(0)
    wav = (wav - ref.mean()) / ref.std()

    with torch.no_grad():
        fontes = apply_model(modelo, wav[None], device=dispositivo, progress=False)[0]
    fontes = fontes * ref.std() + ref.mean()

    # 3) grava cada faixa com soundfile (sem depender de torchcodec) e sobe no Supabase
    supabase_url = os.environ["SUPABASE_URL"].rstrip("/")
    service_key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    bucket = "faixas-separadas"
    faixas = {}

    with httpx.Client(timeout=180) as c:
        for i, nome_demucs in enumerate(modelo.sources):
            nome_pt = STEM_PT.get(nome_demucs, nome_demucs)
            caminho = f"{tmp}/{nome_pt}.wav"
            audio = fontes[i].cpu().numpy().T  # (amostras, canais)
            sf.write(caminho, audio, modelo.samplerate, subtype="PCM_16")

            destino = f"{musica_id}/{nome_pt}.wav"
            with open(caminho, "rb") as f:
                dados = f.read()
            resp = c.post(
                f"{supabase_url}/storage/v1/object/{bucket}/{destino}",
                headers={
                    "Authorization": f"Bearer {service_key}",
                    "apikey": service_key,
                    "Content-Type": "audio/wav",
                    "x-upsert": "true",
                },
                content=dados,
            )
            resp.raise_for_status()
            faixas[nome_pt] = f"{supabase_url}/storage/v1/object/public/{bucket}/{destino}"

    return faixas


@app.function(image=image, secrets=SECRETS)
@modal.fastapi_endpoint(method="POST", docs=False)
def iniciar(body: dict):
    try:
        _checar_chave(str(body.get("chave", "")))
    except PermissionError as e:
        return {"detail": str(e)}, 403
    audio_url = str(body.get("url", "")).strip()
    musica_id = str(body.get("musica_id", "")).strip() or uuid.uuid4().hex
    musica_id = "".join(ch for ch in musica_id if ch.isalnum() or ch in "_-")
    if not audio_url.startswith("https://"):
        return {"detail": "envie 'url' (link https do áudio de referência)"}, 400
    call = separar.spawn(audio_url, musica_id)
    return {"call_id": call.object_id}


@app.function(image=image, secrets=SECRETS)
@modal.fastapi_endpoint(method="POST", docs=False)
def status(body: dict):
    try:
        _checar_chave(str(body.get("chave", "")))
    except PermissionError as e:
        return {"detail": str(e)}, 403
    call_id = str(body.get("call_id", "")).strip()
    if not call_id:
        return {"detail": "envie 'call_id'"}, 400
    try:
        fc = modal.FunctionCall.from_id(call_id)
        faixas = fc.get(timeout=0)
        return {"status": "pronto", "faixas": faixas}
    except TimeoutError:
        return {"status": "processando"}
    except Exception as e:
        return {"status": "erro", "erro": str(e)}
