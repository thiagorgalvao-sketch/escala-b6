-- 19_chat_so_banda_fixa.sql · Garante no servidor que quem escreve SEM login usa um nome da banda fixa
-- Rode uma vez no Supabase: SQL Editor > New query > cole tudo > Run. (Depois do 17 e do 18.)
-- Antes, o app já só mostrava a lista da banda fixa, mas alguém mal-intencionado poderia mandar outro nome direto para o servidor.
create or replace function public.chat_autor()
returns trigger language plpgsql security definer set search_path = public as $$
declare nm text;
begin
  new.texto     := btrim(new.texto);
  new.user_id   := auth.uid();
  new.criado_em := now();
  if auth.uid() is null then
    new.membro_id := null;
    select m.nome into nm from public.membros m
      where m.fixo and m.ativo and lower(btrim(m.nome)) = lower(btrim(coalesce(new.autor, '')))
      limit 1;
    if nm is null then raise exception 'Escolha seu nome na lista da banda fixa para escrever.'; end if;
    new.autor := nm;
    if coalesce(new.device, '') = '' then raise exception 'Aparelho não identificado.'; end if;
    new.device := md5(new.device);
    if (select count(*) from public.chat_mensagens
        where device = new.device and criado_em > now() - interval '1 minute') >= 15 then
      raise exception 'Calma! Muitas mensagens em pouco tempo.';
    end if;
  else
    new.device := null;
    if new.membro_id is not null then
      select nome into new.autor from public.membros where id = new.membro_id;
    end if;
    if coalesce(new.autor, '') = '' then new.autor := 'Liderança'; end if;
  end if;
  return new;
end $$;
