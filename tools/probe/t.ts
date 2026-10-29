import { buscar, cifra, extrair } from "./fn.ts";
const n = (m: string) => console.log("::notice::" + m.replace(/\n/g, "⏎").slice(0, 1500));
try { const r = await buscar("melhor amigo nair nany"); n("BUSCAR " + r.length + " " + JSON.stringify(r.slice(0, 2))); } catch (e) { n("BUSCAR erro " + e); }
try { const r = await buscar("tudo é perda"); n("BUSCAR2 " + r.map((x) => x.titulo + " - " + x.artista).slice(0, 4).join(" | ")); } catch (e) { n("BUSCAR2 erro " + e); }
try { const r = await cifra("nair-nany", "melhor-amigo"); n("CIFRA " + JSON.stringify(r).slice(0, 200)); } catch (e) { n("CIFRA erro " + e); }
const h = `<h1 class="t1">Música &amp; Teste</h1><h2 class="t3"><a href="/x/">Artista X</a></h2><span id="cifra_tom">tom: <a class="js-modal-trigger" href="#">G</a></span><pre>[Intro] <b>G</b>  <b>D/F#</b>\n\n[Primeira Parte]\n\n<b>G</b>        <b>C</b>\nLinha um da letra\n</pre>`;
n("EXTRAIR " + JSON.stringify(extrair(h)));
