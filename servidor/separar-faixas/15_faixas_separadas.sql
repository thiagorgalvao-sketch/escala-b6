-- Fervor · 15 · Separação de faixas por instrumento (vocal, bateria, baixo, guitarra, teclado)
-- Cole no SQL Editor do Supabase e clique em Run. Depois siga os passos no final
-- (criar o segredo com a chave do serviço no Modal).
--
-- Atualização: se você já tinha rodado esta função antes, rode este arquivo de novo —
-- ele só sobe o limite de tamanho do arquivo (de 50 MB para 250 MB), nada mais muda.
-- O resto dos passos (função, segredos) você não precisa refazer.

-- Pasta pública "faixas-separadas" no Storage — guarda o áudio original enviado
-- (pasta _origem/) e os 6 arquivos wav resultantes de cada música (vocal, bateria,
-- baixo, guitarra, teclado, outros). As faixas agora são salvas em WAV (sem perda de
-- qualidade), bem maiores que mp3, por isso o limite subiu de 50 MB para 250 MB por arquivo.
insert into storage.buckets (id, name, public, file_size_limit)
values ('faixas-separadas', 'faixas-separadas', true, 262144000)
on conflict (id) do update set public = true, file_size_limit = 262144000;

drop policy if exists "b6 faixas ler"     on storage.objects;
drop policy if exists "b6 faixas enviar"  on storage.objects;
drop policy if exists "b6 faixas alterar" on storage.objects;
drop policy if exists "b6 faixas apagar"  on storage.objects;
create policy "b6 faixas ler"     on storage.objects for select using (bucket_id = 'faixas-separadas');
create policy "b6 faixas enviar"  on storage.objects for insert to authenticated with check (bucket_id = 'faixas-separadas' and public.is_admin());
create policy "b6 faixas alterar" on storage.objects for update to authenticated using (bucket_id = 'faixas-separadas' and public.is_admin()) with check (bucket_id = 'faixas-separadas' and public.is_admin());
create policy "b6 faixas apagar"  on storage.objects for delete to authenticated using (bucket_id = 'faixas-separadas' and public.is_admin());

select 'ok: pasta de faixas separadas pronta — falta publicar a função e os segredos (veja abaixo)' as status;

-- ============================================================================
-- PRÓXIMOS PASSOS (fora do SQL Editor):
--
-- 1) Publique a função "separar-faixas": Supabase → Edge Functions → New Function
--    → cole o conteúdo de funcao_separar-faixas/index.ts.
--
-- 2) Adicione três segredos, em Edge Functions → Secrets:
--      MODAL_INICIAR_URL = https://thiagorgalvao-sketch--fervor-separador-faixas-iniciar.us-east.modal.run
--      MODAL_STATUS_URL  = https://thiagorgalvao-sketch--fervor-separador-faixas-status.us-east.modal.run
--      MODAL_API_KEY     = (a mesma senha que você colocou no secret API_KEY do Modal)
--
--    (SUPABASE_URL e SUPABASE_ANON_KEY já existem automaticamente em toda função.)
--
-- 3) No Modal, além do secret "API_KEY" que já existe, crie outro chamado
--    "fervor-supabase" (Secrets → Create new secret → Custom) com duas chaves:
--      SUPABASE_URL = https://hofrthndlstofytlapzk.supabase.co
--      SUPABASE_SERVICE_ROLE_KEY = (em Supabase: Project Settings → API → service_role secret key)
--    Esse é o que permite o Modal subir as faixas prontas direto no Storage.
-- ============================================================================
