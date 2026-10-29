// Fervor · Edge Function "buscar-cifra"
// 1) "buscar": procura músicas no índice de busca do Cifra Club (nome, artista, link e foto).
// 2) "cifra": tenta baixar a cifra da página da música (tom, título, artista e texto da cifra).
//    O Cifra Club costuma bloquear servidores; quando isso acontecer, a função avisa
//    ("bloqueado") e o app oferece o botão "Enviar ao Fervor" para importar pelo navegador.
// Só administradores (logados no app) conseguem chamar.
import { createClient } from "npm:@supabase/supabase-js@2";

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
const json = (o: unknown, status = 200) =>
  new Response(JSON.stringify(o), { status, headers: { ...cors, "Content-Type": "application/json" } });
const UA = {
  "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36",
  "Accept": "text/html,application/json,*/*",
  "Accept-Language": "pt-BR,pt;q=0.9",
};
const SLUG = /^[a-z0-9-]{1,160}$/;
const ent = (s: string) =>
  s.replace(/&#(\d+);/g, (_, n) => String.fromCharCode(+n)).replace(/&#x([0-9a-f]+);/gi, (_, n) => String.fromCharCode(parseInt(n, 16)))
    .replace(/&quot;/g, '"').replace(/&apos;|&#39;/g, "'").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&nbsp;/g, " ").replace(/&amp;/g, "&");
const txt = (s: string) => ent(s.replace(/<br\s*\/?>/gi, "\n").replace(/<[^>]+>/g, "")).replace(/\r/g, "");

export async function buscar(q: string) {
  const r = await fetch("https://solr.sscdn.co/cc/c7/?q=" + encodeURIComponent(q), { headers: UA });
  if (!r.ok) throw new Error("busca indisponível (" + r.status + ")");
  const j = await r.json();
  return ((j?.response?.docs ?? []) as Record<string, string>[])
    .filter((d) => d.dns && d.url && d.txt)
    .slice(0, 12)
    .map((d) => ({ titulo: d.txt, artista: d.art ?? "", dns: d.dns, url: d.url, foto: d.imgm ?? "", link: `https://www.cifraclub.com.br/${d.dns}/${d.url}/` }));
}

export function extrair(html: string) {
  const pre = html.match(/<pre[^>]*>([\s\S]*?)<\/pre>/i);
  if (!pre) return null;
  const cifra = txt(pre[1]).replace(/\n{3,}/g, "\n\n").trim();
  const tomM = html.match(/id="cifra_tom"[\s\S]{0,400}?<a[^>]*>\s*([A-G][#b]?m?)\s*</i);
  const h1 = html.match(/<h1[^>]*>([\s\S]*?)<\/h1>/i), h2 = html.match(/<h2[^>]*>([\s\S]*?)<\/h2>/i);
  return { cifra, tom: tomM ? tomM[1] : "", titulo: h1 ? txt(h1[1]).trim() : "", artista: h2 ? txt(h2[1]).trim() : "" };
}

export async function cifra(dns: string, url: string) {
  if (!SLUG.test(dns) || !SLUG.test(url)) throw new Error("link inválido");
  const link = `https://www.cifraclub.com.br/${dns}/${url}/`;
  const r = await fetch(link, { headers: { ...UA, Referer: "https://www.cifraclub.com.br/" } });
  if (r.status === 403 || r.status === 429) return { bloqueado: true, link };
  if (!r.ok) throw new Error("página indisponível (" + r.status + ")");
  const e = extrair(await r.text());
  if (!e || e.cifra.length < 20) return { bloqueado: true, link };
  return { ok: true, link, ...e };
}

if (!Deno.env.get("FV_TESTE")) Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  if (req.method !== "POST") return json({ erro: "use POST" }, 405);
  try {
    const quem = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_ANON_KEY")!, {
      global: { headers: { Authorization: req.headers.get("Authorization") ?? "" } },
    });
    const { data: ok } = await quem.rpc("is_admin");
    if (ok !== true) return json({ erro: "sem permissão" }, 403);
    const b = await req.json().catch(() => ({}));
    if (b.acao === "buscar") {
      const q = String(b.q || "").trim().slice(0, 120);
      if (q.length < 2) return json({ erro: "digite o nome da música" }, 400);
      return json({ ok: true, itens: await buscar(q) });
    }
    if (b.acao === "cifra") return json(await cifra(String(b.dns || ""), String(b.url || "")));
    return json({ erro: "ação desconhecida" }, 400);
  } catch (e) {
    return json({ erro: String((e as Error)?.message ?? e) }, 500);
  }
});
