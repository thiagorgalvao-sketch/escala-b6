-- 18_chat_membros_fixos.sql · Lista (só nomes) dos integrantes da banda FIXA, para quem abre o chat sem login escolher quem é
-- Rode uma vez no Supabase: SQL Editor > New query > cole tudo > Run. (Depois do 17_chat_publico.sql.)
-- Só devolve o nome de quem está marcado como "Banda fixa" e "Ativo" em Acesso da banda. Nenhum outro dado sai daqui.
create or replace function public.chat_membros()
returns table (nome text) language sql stable security definer set search_path = public as $$
  select m.nome from public.membros m
  where m.fixo and m.ativo and public.chat_ativo()
  order by m.nome;
$$;
grant execute on function public.chat_membros() to anon, authenticated;
