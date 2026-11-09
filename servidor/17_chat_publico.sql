-- 17_chat_publico.sql · Chat para quem abre o app SEM login + liga/desliga do chat (Ajustes de admin)
-- Rode uma vez no Supabase: SQL Editor > New query > cole tudo > Run. (Precisa do 16_chat.sql já rodado.)

-- 1) Liga/desliga: valor 'true' = chat ligado (padrão). A banda lê esta chave sem login.
insert into public.config (chave, valor) values ('chat_ativo', 'true'::jsonb) on conflict (chave) do nothing;
drop policy if exists config_select on public.config;
create policy config_select on public.config for select to anon, authenticated
  using (chave in ('login_banda','whats_contato','nome_contato','chat_ativo'));

create or replace function public.chat_ativo()
returns boolean language sql stable security definer set search_path = public as $$
  select coalesce((select valor = 'true'::jsonb from public.config where chave = 'chat_ativo'), true);
$$;
grant execute on function public.chat_ativo() to anon, authenticated;

-- 2) Mensagens de quem não tem login: guardam um "carimbo" do aparelho (só o hash, para poder apagar a própria mensagem)
alter table public.chat_mensagens alter column user_id drop not null;
alter table public.chat_mensagens add column if not exists device text;

create or replace function public.chat_autor()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  new.texto     := btrim(new.texto);
  new.user_id   := auth.uid();
  new.criado_em := now();
  if auth.uid() is null then
    -- sem login: nome escolhido na lista da banda + carimbo do aparelho
    new.membro_id := null;
    new.autor     := left(btrim(coalesce(new.autor, '')), 40);
    if new.autor = '' then raise exception 'Escolha quem você é para escrever.'; end if;
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

-- 3) Permissões: chat ligado => lê/escreve quem tem login (como antes) e também quem abre sem login
drop policy if exists chat_select on public.chat_mensagens;
drop policy if exists chat_insert on public.chat_mensagens;
drop policy if exists chat_select_anon on public.chat_mensagens;
drop policy if exists chat_insert_anon on public.chat_mensagens;
create policy chat_select on public.chat_mensagens for select to authenticated
  using (public.chat_ativo() and public.is_membro());
create policy chat_insert on public.chat_mensagens for insert to authenticated
  with check (public.chat_ativo() and public.is_membro() and (public.is_admin()
    or membro_id in (select id from public.membros where user_id = auth.uid() and ativo)));
create policy chat_select_anon on public.chat_mensagens for select to anon
  using (public.chat_ativo());
create policy chat_insert_anon on public.chat_mensagens for insert to anon
  with check (public.chat_ativo() and char_length(coalesce(device, '')) between 8 and 64);

-- 4) Quem escreveu sem login apaga só a própria mensagem (confere o carimbo do aparelho)
create or replace function public.chat_apagar(p_id bigint, p_device text)
returns boolean language plpgsql security definer set search_path = public as $$
declare n int;
begin
  delete from public.chat_mensagens where id = p_id and device is not null and device = md5(coalesce(p_device, ''));
  get diagnostics n = row_count;
  return n > 0;
end $$;
grant execute on function public.chat_apagar(bigint, text) to anon, authenticated;
