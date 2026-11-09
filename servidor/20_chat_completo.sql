-- 20_chat_completo.sql · Chat completo: responder citando, reações, "visto por", enquetes, áudio,
-- mensagem fixada, moderação (palavras bloqueadas, silenciar, denúncias), números do chat e avisos no celular.
-- Rode uma vez no Supabase: SQL Editor > New query > cole tudo > Run. (Depois do 16, 17, 18 e 19.)

-- 1) Novas colunas nas mensagens
alter table public.chat_mensagens add column if not exists resp_id bigint;
alter table public.chat_mensagens add column if not exists tipo text not null default 'txt';
alter table public.chat_mensagens add column if not exists extra jsonb;
alter table public.chat_mensagens add column if not exists fixada boolean not null default false;
alter table public.chat_mensagens add column if not exists avisado boolean not null default false;
alter table public.push_subs add column if not exists chat boolean not null default false;
alter table public.push_subs add column if not exists quem text;
alter table public.chat_mensagens drop constraint if exists chat_tipo_ok;
alter table public.chat_mensagens add constraint chat_tipo_ok check (tipo in ('txt','audio','enquete'));

-- 2) Quem é a pessoa (conta logada ou aparelho sem login) e qual nome ela pode usar
create or replace function public.chat_quem(p_device text)
returns text language sql stable as $$
  select case when auth.uid() is not null then 'u:' || auth.uid()::text
              else 'd:' || md5(coalesce(p_device, '')) end;
$$;

create or replace function public.chat_nome(p_nome text)
returns text language plpgsql stable security definer set search_path = public as $$
declare nm text;
begin
  if auth.uid() is not null then
    select nome into nm from public.membros where user_id = auth.uid() limit 1;
    return coalesce(nm, nullif(left(btrim(coalesce(p_nome, '')), 40), ''), 'Liderança');
  end if;
  select m.nome into nm from public.membros m
   where m.fixo and m.ativo and lower(btrim(m.nome)) = lower(btrim(coalesce(p_nome, ''))) limit 1;
  if nm is null then raise exception 'Escolha seu nome na lista da banda fixa.'; end if;
  return nm;
end $$;

create or replace function public.chat_pode()
returns boolean language sql stable security definer set search_path = public as $$
  select public.chat_ativo() and (auth.uid() is null or public.is_membro());
$$;
grant execute on function public.chat_pode() to anon, authenticated;

-- 3) Moderação: palavras bloqueadas e pessoas silenciadas (a liderança edita no app; ninguém mais lê)
insert into public.config (chave, valor) values ('chat_bloqueio', '[]'::jsonb) on conflict (chave) do nothing;
insert into public.config (chave, valor) values ('chat_silenciados', '[]'::jsonb) on conflict (chave) do nothing;

create or replace function public.chat_moderar(p_nome text, p_texto text)
returns void language plpgsql stable security definer set search_path = public as $$
declare w text;
begin
  if auth.uid() is not null and public.is_admin() then return; end if;
  if exists (select 1 from public.config c, jsonb_array_elements_text(coalesce(c.valor, '[]'::jsonb)) s
             where c.chave = 'chat_silenciados' and lower(btrim(s)) = lower(btrim(coalesce(p_nome, '')))) then
    raise exception 'Você está silenciado no chat pela liderança.';
  end if;
  for w in select lower(btrim(s)) from public.config c, jsonb_array_elements_text(coalesce(c.valor, '[]'::jsonb)) s
           where c.chave = 'chat_bloqueio' loop
    if w <> '' and position(w in lower(coalesce(p_texto, ''))) > 0 then
      raise exception 'Mensagem bloqueada pela moderação.';
    end if;
  end loop;
end $$;

-- 4) Regras ao gravar uma mensagem (nome, tipo, áudio, enquete, resposta, moderação)
create or replace function public.chat_autor()
returns trigger language plpgsql security definer set search_path = public as $$
declare nm text; n int;
begin
  new.texto     := btrim(new.texto);
  new.user_id   := auth.uid();
  new.criado_em := now();
  new.fixada    := false;
  new.avisado   := false;
  new.tipo      := coalesce(new.tipo, 'txt');
  if auth.uid() is null then
    new.membro_id := null;
    select m.nome into nm from public.membros m
      where m.fixo and m.ativo and lower(btrim(m.nome)) = lower(btrim(coalesce(new.autor, ''))) limit 1;
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
  perform public.chat_moderar(new.autor, new.texto);
  if new.tipo = 'audio' then
    if coalesce(new.extra->>'url', '') !~ '^https://[a-z0-9]+\.supabase\.co/storage/v1/object/public/chat/' then
      raise exception 'Áudio inválido.';
    end if;
    new.extra := jsonb_build_object('url', new.extra->>'url', 'dur', least(greatest(coalesce((new.extra->>'dur')::int, 0), 0), 120));
  elsif new.tipo = 'enquete' then
    n := coalesce(jsonb_array_length(new.extra->'o'), 0);
    if n < 2 or n > 6 then raise exception 'A enquete precisa de 2 a 6 opções.'; end if;
    new.extra := jsonb_build_object('o', (select jsonb_agg(left(btrim(x), 80)) from jsonb_array_elements_text(new.extra->'o') x));
  else
    new.extra := case when new.extra ? 'rq' then jsonb_build_object('rq', jsonb_build_object(
                   'a', left(new.extra->'rq'->>'a', 40), 't', left(new.extra->'rq'->>'t', 120))) else null end;
  end if;
  if new.resp_id is not null and not exists (select 1 from public.chat_mensagens where id = new.resp_id) then
    new.resp_id := null;
  end if;
  return new;
end $$;

-- 5) Reações, votos de enquete, "visto por" e denúncias
create table if not exists public.chat_reacoes (
  msg_id bigint not null references public.chat_mensagens(id) on delete cascade,
  quem   text not null,
  nome   text not null,
  emoji  text not null,
  em     timestamptz not null default now(),
  primary key (msg_id, quem)
);
create table if not exists public.chat_votos (
  msg_id bigint not null references public.chat_mensagens(id) on delete cascade,
  quem   text not null,
  nome   text not null,
  opcao  int  not null,
  em     timestamptz not null default now(),
  primary key (msg_id, quem)
);
create table if not exists public.chat_lidos (
  quem   text primary key,
  nome   text not null,
  ultimo bigint not null default 0,
  em     timestamptz not null default now()
);
create table if not exists public.chat_denuncias (
  id     bigint generated always as identity primary key,
  msg_id bigint not null references public.chat_mensagens(id) on delete cascade,
  quem   text not null,
  nome   text not null,
  motivo text,
  em     timestamptz not null default now(),
  unique (msg_id, quem)
);
alter table public.chat_reacoes   enable row level security;
alter table public.chat_votos     enable row level security;
alter table public.chat_lidos     enable row level security;
alter table public.chat_denuncias enable row level security;
-- (sem políticas: só se lê e grava pelas funções abaixo)

create or replace function public.chat_reagir(p_msg bigint, p_emoji text, p_device text, p_nome text)
returns void language plpgsql security definer set search_path = public as $$
declare q text := public.chat_quem(p_device); nm text;
begin
  if not public.chat_pode() then raise exception 'Chat indisponível.'; end if;
  if char_length(coalesce(p_emoji, '')) not between 1 and 8 then raise exception 'Reação inválida.'; end if;
  nm := public.chat_nome(p_nome);
  if exists (select 1 from public.chat_reacoes where msg_id = p_msg and quem = q and emoji = p_emoji) then
    delete from public.chat_reacoes where msg_id = p_msg and quem = q;
  else
    insert into public.chat_reacoes (msg_id, quem, nome, emoji) values (p_msg, q, nm, p_emoji)
      on conflict (msg_id, quem) do update set emoji = excluded.emoji, nome = excluded.nome, em = now();
  end if;
end $$;

create or replace function public.chat_votar(p_msg bigint, p_op int, p_device text, p_nome text)
returns void language plpgsql security definer set search_path = public as $$
declare q text := public.chat_quem(p_device); nm text; n int;
begin
  if not public.chat_pode() then raise exception 'Chat indisponível.'; end if;
  select jsonb_array_length(extra->'o') into n from public.chat_mensagens where id = p_msg and tipo = 'enquete';
  if n is null or p_op < 0 or p_op >= n then raise exception 'Opção inválida.'; end if;
  nm := public.chat_nome(p_nome);
  if exists (select 1 from public.chat_votos where msg_id = p_msg and quem = q and opcao = p_op) then
    delete from public.chat_votos where msg_id = p_msg and quem = q;
  else
    insert into public.chat_votos (msg_id, quem, nome, opcao) values (p_msg, q, nm, p_op)
      on conflict (msg_id, quem) do update set opcao = excluded.opcao, nome = excluded.nome, em = now();
  end if;
end $$;

create or replace function public.chat_li(p_ult bigint, p_device text, p_nome text)
returns void language plpgsql security definer set search_path = public as $$
declare q text := public.chat_quem(p_device); nm text;
begin
  if not public.chat_pode() then return; end if;
  nm := public.chat_nome(p_nome);
  insert into public.chat_lidos (quem, nome, ultimo) values (q, nm, greatest(coalesce(p_ult, 0), 0))
    on conflict (quem) do update set ultimo = greatest(public.chat_lidos.ultimo, excluded.ultimo), nome = excluded.nome, em = now();
end $$;

create or replace function public.chat_denunciar(p_msg bigint, p_motivo text, p_device text, p_nome text)
returns void language plpgsql security definer set search_path = public as $$
declare q text := public.chat_quem(p_device); nm text;
begin
  if not public.chat_pode() then raise exception 'Chat indisponível.'; end if;
  nm := public.chat_nome(p_nome);
  insert into public.chat_denuncias (msg_id, quem, nome, motivo) values (p_msg, q, nm, left(btrim(coalesce(p_motivo, '')), 200))
    on conflict (msg_id, quem) do nothing;
end $$;

-- Tudo o que acompanha as mensagens, numa consulta só (reações, votos, quem leu, fixada, denúncias)
create or replace function public.chat_extras(p_desde bigint, p_device text)
returns jsonb language plpgsql stable security definer set search_path = public as $$
declare q text := public.chat_quem(p_device);
begin
  if not public.chat_pode() then return null; end if;
  return jsonb_build_object(
    'r', (select coalesce(jsonb_agg(jsonb_build_array(msg_id, emoji, nome, quem = q)), '[]'::jsonb) from public.chat_reacoes where msg_id >= coalesce(p_desde, 0)),
    'v', (select coalesce(jsonb_agg(jsonb_build_array(msg_id, opcao, nome, quem = q)), '[]'::jsonb) from public.chat_votos where msg_id >= coalesce(p_desde, 0)),
    'l', (select coalesce(jsonb_agg(jsonb_build_array(nome, ultimo, quem = q)), '[]'::jsonb) from public.chat_lidos where em > now() - interval '60 days'),
    'f', (select to_jsonb(x) from (select id, autor, texto, tipo, criado_em from public.chat_mensagens where fixada order by id desc limit 1) x),
    'd', (case when auth.uid() is not null and public.is_admin() then (select count(*) from public.chat_denuncias) else null end));
end $$;

-- 6) Liderança: fixar mensagem, ver denúncias e números do chat
create or replace function public.chat_fixar(p_id bigint, p_on boolean)
returns void language plpgsql security definer set search_path = public as $$
begin
  if auth.uid() is null or not public.is_admin() then raise exception 'Só a liderança fixa mensagens.'; end if;
  update public.chat_mensagens set fixada = false where fixada;
  if p_on then update public.chat_mensagens set fixada = true where id = p_id; end if;
end $$;

create or replace function public.chat_denuncias_lista()
returns jsonb language sql stable security definer set search_path = public as $$
  select case when auth.uid() is not null and public.is_admin() then coalesce((
    select jsonb_agg(jsonb_build_object('id', m.id, 'autor', m.autor, 'texto', m.texto, 'qtd', d.qtd, 'por', d.por, 'motivos', d.motivos) order by d.ult desc)
    from (select msg_id, count(*) qtd, string_agg(nome, ', ') por, string_agg(nullif(motivo, ''), ' · ') motivos, max(em) ult
          from public.chat_denuncias group by msg_id) d
    join public.chat_mensagens m on m.id = d.msg_id), '[]'::jsonb) end;
$$;

create or replace function public.chat_numeros()
returns jsonb language sql stable security definer set search_path = public as $$
  select case when auth.uid() is not null and public.is_admin() then jsonb_build_object(
    'm7',  (select count(*) from public.chat_mensagens where criado_em > now() - interval '7 days'),
    'm30', (select count(*) from public.chat_mensagens where criado_em > now() - interval '30 days'),
    'p7',  (select count(distinct autor) from public.chat_mensagens where criado_em > now() - interval '7 days'),
    'top', (select coalesce(jsonb_agg(jsonb_build_array(autor, n)), '[]'::jsonb) from (
              select autor, count(*) n from public.chat_mensagens where criado_em > now() - interval '30 days'
              group by autor order by n desc limit 5) t),
    'lendo', (select count(*) from public.chat_lidos where em > now() - interval '7 days'),
    'avisos', (select count(*) from public.push_subs where chat),
    'resp', (select round(avg(extract(epoch from (r.criado_em - o.criado_em)) / 60)::numeric, 0) from public.chat_mensagens r
              join public.chat_mensagens o on o.id = r.resp_id where r.criado_em > now() - interval '30 days'),
    'reac', (select count(*) from public.chat_reacoes where em > now() - interval '30 days')) end;
$$;

create or replace function public.chat_denuncia_limpar(p_msg bigint)
returns void language plpgsql security definer set search_path = public as $$
begin
  if auth.uid() is null or not public.is_admin() then raise exception 'Só a liderança.'; end if;
  delete from public.chat_denuncias where msg_id = p_msg;
end $$;
revoke all on function public.chat_denuncia_limpar(bigint) from public;
grant execute on function public.chat_denuncia_limpar(bigint) to authenticated;

-- 7) Avisos no celular para o chat (usa a mesma lista de celulares dos avisos de repertório)

create or replace function public.chat_aviso_salvar(ep text, p256dh text, au text, p_device text, p_on boolean)
returns void language plpgsql security definer set search_path = public as $$
begin
  insert into public.push_subs (endpoint, p256dh, auth, chat, quem)
  values (left(ep, 1000), left(p256dh, 200), left(au, 100), coalesce(p_on, true), public.chat_quem(p_device))
  on conflict (endpoint) do update set p256dh = excluded.p256dh, auth = excluded.auth, chat = excluded.chat, quem = excluded.quem;
end $$;

-- 8) Áudios do chat (pasta pública "chat", até 3 MB, só áudio)
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('chat', 'chat', true, 3145728, array['audio/webm','audio/mp4','audio/mpeg','audio/ogg','audio/aac','audio/x-m4a','audio/wav'])
on conflict (id) do update set public = true, file_size_limit = excluded.file_size_limit, allowed_mime_types = excluded.allowed_mime_types;
drop policy if exists "fervor chat audio enviar" on storage.objects;
create policy "fervor chat audio enviar" on storage.objects for insert to anon, authenticated
  with check (bucket_id = 'chat' and (storage.foldername(name))[1] = 'a' and public.chat_ativo());

-- 9) Permissões das funções
revoke all on function public.chat_reagir(bigint, text, text, text)        from public;
revoke all on function public.chat_votar(bigint, int, text, text)          from public;
revoke all on function public.chat_li(bigint, text, text)                  from public;
revoke all on function public.chat_denunciar(bigint, text, text, text)     from public;
revoke all on function public.chat_extras(bigint, text)                    from public;
revoke all on function public.chat_fixar(bigint, boolean)                  from public;
revoke all on function public.chat_denuncias_lista()                       from public;
revoke all on function public.chat_numeros()                               from public;
revoke all on function public.chat_aviso_salvar(text, text, text, text, boolean) from public;
grant execute on function public.chat_reagir(bigint, text, text, text)     to anon, authenticated;
grant execute on function public.chat_votar(bigint, int, text, text)       to anon, authenticated;
grant execute on function public.chat_li(bigint, text, text)               to anon, authenticated;
grant execute on function public.chat_denunciar(bigint, text, text, text)  to anon, authenticated;
grant execute on function public.chat_extras(bigint, text)                 to anon, authenticated;
grant execute on function public.chat_aviso_salvar(text, text, text, text, boolean) to anon, authenticated;
grant execute on function public.chat_fixar(bigint, boolean)               to authenticated;
grant execute on function public.chat_denuncias_lista()                    to authenticated;
grant execute on function public.chat_numeros()                            to authenticated;

select 'ok: chat completo pronto' as status;
