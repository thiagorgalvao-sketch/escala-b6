-- 22_chat_limite_upload.sql · Limite de uploads de áudio no chat (evita flood na cota do Supabase)
-- Rode uma vez no Supabase: SQL Editor > New query > cole tudo > Run. (Depois do 20_chat_completo.sql.)
-- Até agora, quem sabia a URL de upload podia mandar áudios de até 3 MB sem limite nenhum,
-- mesmo sem nunca criar uma mensagem (o limite de "15 mensagens por minuto" só vale para a mensagem,
-- não para o arquivo de áudio em si). Isto trava o total de áudios novos em 30 por minuto, na soma de todo mundo.

drop policy if exists "fervor chat audio enviar" on storage.objects;
create policy "fervor chat audio enviar" on storage.objects for insert to anon, authenticated
  with check (
    bucket_id = 'chat' and (storage.foldername(name))[1] = 'a' and public.chat_ativo()
    and (select count(*) from storage.objects where bucket_id = 'chat' and created_at > now() - interval '1 minute') < 30
  );

select 'ok: limite de upload de áudio no chat' as status;
