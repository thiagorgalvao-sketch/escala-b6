// Fervor · Edge Function "chat-aviso"
// Avisa no celular quando chega mensagem nova no chat da banda.
// O app chama esta função logo depois de enviar uma mensagem, passando só o número dela.
// A função confere no banco se a mensagem é nova (menos de 3 minutos) e ainda não foi avisada,
// por isso ninguém consegue usá-la para mandar avisos falsos ou repetidos.
// Versão 2: avisa quem foi mencionado (@nome) mesmo com os avisos do chat desligados, e respeita
// quem pediu para não mostrar o texto da mensagem no aviso.
// Ao criar a função no Supabase, DESLIGUE a opção "Verify JWT" (quem está sem login também envia mensagens).
import webpush from "npm:web-push@3.6.7";
import { createClient } from "npm:@supabase/supabase-js@2";

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
const json = (o: unknown, status = 200) =>
  new Response(JSON.stringify(o), { status, headers: { ...cors, "Content-Type": "application/json" } });
const SITE = "https://fervor.website/";

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  if (req.method !== "POST") return json({ erro: "use POST" }, 405);
  try {
    const pub = Deno.env.get("VAPID_PUBLIC_KEY");
    const priv = Deno.env.get("VAPID_PRIVATE_KEY");
    if (!pub || !priv) return json({ erro: "faltam as chaves VAPID nos segredos" }, 500);
    const db = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!);

    const b = await req.json().catch(() => ({}));
    const id = Number(b.id);
    if (!Number.isFinite(id) || id <= 0) return json({ erro: "id inválido" }, 400);

    const { data: cfg } = await db.from("config").select("valor").eq("chave", "chat_ativo").maybeSingle();
    if (cfg && cfg.valor === false) return json({ enviados: 0, motivo: "chat desligado" });

    // marca como avisada (uma vez só) e lê a mensagem
    const desde = new Date(Date.now() - 3 * 60 * 1000).toISOString();
    const { data: m } = await db.from("chat_mensagens").update({ avisado: true })
      .eq("id", id).eq("avisado", false).gte("criado_em", desde)
      .select("id,autor,texto,tipo,user_id,device").maybeSingle();
    if (!m) return json({ enviados: 0, motivo: "mensagem já avisada ou antiga" });

    const autorQuem = m.user_id ? "u:" + m.user_id : "d:" + m.device;
    const texto = String(m.texto || "");
    // menções: [[p:...|Nome]] -> "Nome"
    const mencionados = [...texto.matchAll(/\[\[p:[^|\]]*\|([^\]]+)\]\]/g)].map((x) => x[1].trim().toLowerCase());
    const limpo = texto.replace(/\[\[(m|c|p):[^|\]]*\|([^\]]+)\]\]/g, (_x, k, n) => (k === "p" ? "@" : "") + n);
    const corpo = m.tipo === "audio" ? "🎤 Mensagem de voz" : m.tipo === "enquete" ? "📊 Enquete: " + limpo : limpo;
    let quemMenc = new Set<string>();
    if (mencionados.length) {
      const { data: li } = await db.from("chat_lidos").select("quem,nome");
      quemMenc = new Set((li ?? []).filter((x) => mencionados.includes(String(x.nome).trim().toLowerCase())).map((x) => x.quem));
    }
    const carga = (menc: boolean, previa: boolean) => JSON.stringify({
      title: previa ? (menc ? "📣 " + String(m.autor).slice(0, 50) + " mencionou você" : "💬 " + String(m.autor || "Chat da banda").slice(0, 60)) : "Fervor",
      body: previa ? corpo.slice(0, 200) : (menc ? "Você foi mencionado no chat da banda" : "Nova mensagem no chat da banda"),
      url: SITE + "#chat",
      tag: "chat",
    });

    webpush.setVapidDetails(SITE, pub, priv);
    const { data: subs, error } = await db.from("push_subs").select("endpoint,p256dh,auth,quem,chat,previa");
    if (error) return json({ erro: error.message }, 500);

    let enviados = 0, removidos = 0, falhas = 0;
    await Promise.all((subs ?? []).filter((s) => s.quem !== autorQuem && (s.chat || (s.quem && quemMenc.has(s.quem)))).map(async (s) => {
      try {
        const menc = !!s.quem && quemMenc.has(s.quem);
        await webpush.sendNotification({ endpoint: s.endpoint, keys: { p256dh: s.p256dh, auth: s.auth } }, carga(menc, s.previa !== false), { TTL: 3600, urgency: "high" });
        enviados++;
      } catch (e) {
        const st = (e as { statusCode?: number }).statusCode;
        if (st === 404 || st === 410) { removidos++; await db.from("push_subs").delete().eq("endpoint", s.endpoint); }
        else falhas++;
      }
    }));
    return json({ enviados, removidos, falhas });
  } catch (e) {
    return json({ erro: String((e as Error)?.message ?? e) }, 500);
  }
});
