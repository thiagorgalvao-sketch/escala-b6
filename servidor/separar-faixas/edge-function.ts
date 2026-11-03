// Fervor · Edge Function "separar-faixas"
// Ponte fina entre o app e o serviço no Modal. Só administradores chamam.
// O Modal faz todo o trabalho pesado (e sobe as faixas direto no Storage do
// Supabase com a chave de serviço); essa função só repassa duas ações rápidas,
// pra nunca ficar presa esperando (o plano gratuito do Supabase derruba a
// função se ela passar de ~150s rodando):
//   {acao:"iniciar", url, musica_id} → começa a separação, devolve um call_id
//   {acao:"status", call_id}         → pergunta "já terminou?"
import { createClient } from "npm:@supabase/supabase-js@2";

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
const json = (o: unknown, status = 200) =>
  new Response(JSON.stringify(o), { status, headers: { ...cors, "Content-Type": "application/json" } });

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  if (req.method !== "POST") return json({ erro: "use POST" }, 405);
  try {
    const url = Deno.env.get("SUPABASE_URL")!;
    const anon = Deno.env.get("SUPABASE_ANON_KEY")!;
    const modalIniciar = Deno.env.get("MODAL_INICIAR_URL");
    const modalStatus = Deno.env.get("MODAL_STATUS_URL");
    const modalKey = Deno.env.get("MODAL_API_KEY");
    if (!modalIniciar || !modalStatus || !modalKey) {
      return json({ erro: "faltam MODAL_INICIAR_URL / MODAL_STATUS_URL / MODAL_API_KEY nos segredos da função" }, 500);
    }

    // quem chamou é administrador?
    const auth = req.headers.get("Authorization") ?? "";
    const quem = createClient(url, anon, { global: { headers: { Authorization: auth } } });
    const { data: ok } = await quem.rpc("is_admin");
    if (ok !== true) return json({ erro: "sem permissão" }, 403);

    const b = await req.json().catch(() => ({}));
    const acao = String(b.acao || "");

    if (acao === "iniciar") {
      const audioUrl = String(b.url || "").trim();
      const musicaId = String(b.musica_id || "").trim().replace(/[^a-zA-Z0-9_-]/g, "") || crypto.randomUUID();
      if (!audioUrl || !/^https:\/\//.test(audioUrl)) return json({ erro: "envie 'url' (link https do áudio de referência)" }, 400);
      const resp = await fetch(modalIniciar, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ chave: modalKey, url: audioUrl, musica_id: musicaId }),
      });
      const corpo = await resp.json().catch(() => ({}));
      if (!resp.ok) return json({ erro: corpo.detail || `o serviço respondeu ${resp.status}` }, 502);
      return json({ ok: true, call_id: corpo.call_id });
    }

    if (acao === "status") {
      const callId = String(b.call_id || "").trim();
      if (!callId) return json({ erro: "envie 'call_id'" }, 400);
      const resp = await fetch(modalStatus, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ chave: modalKey, call_id: callId }),
      });
      const corpo = await resp.json().catch(() => ({}));
      if (!resp.ok) return json({ erro: corpo.detail || `o serviço respondeu ${resp.status}` }, 502);
      return json(corpo);
    }

    return json({ erro: "'acao' precisa ser 'iniciar' ou 'status'" }, 400);
  } catch (e) {
    return json({ erro: String((e as Error)?.message ?? e) }, 500);
  }
});
