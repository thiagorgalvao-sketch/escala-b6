-- 21_chat_jeito_apple.sql · Editar mensagem (até 15 min), esconder "visto por", ocultar o texto nos avisos
-- Rode uma vez no Supabase: SQL Editor > New query > cole tudo > Run. (Depois do 20_chat_completo.sql.)

alter table public.chat_mensagens add column if not exists editado_em timestamptz;
alter table public.push_subs add column if not exists previa boolean not null default true;

-- Editar a própria mensagem de texto até 15 minutos depois de enviar
create or replace function public.chat_editar(p_id bigint, p_texto text, p_device text)
returns jsonb language plpgsql security definer set search_path = public as $$
declare m public.chat_mensagens; t text := btrim(coalesce(p_texto, ''));
begin
  if not public.chat_pode() then raise exception 'Chat indisponível.'; end if;
  select * into m from public.chat_mensagens where id = p_id;
  if m.id is null then raise exception 'Mensagem não encontrada.'; end if;
  if not ((auth.uid() is not null and m.user_id = auth.uid())
          or (auth.uid() is null and m.device is not null and m.device = md5(coalesce(p_device, '')))) then
    raise exception 'Você só pode editar as suas mensagens.';
  end if;
  if m.tipo <> 'txt' then raise exception 'Só dá para editar mensagens de texto.'; end if;
  if m.criado_em < now() - interval '15 minutes' then raise exception 'Só dá para editar até 15 minutos depois de enviar.'; end if;
  if char_length(t) not between 1 and 2000 then raise exception 'Mensagem vazia ou grande demais.'; end if;
  perform public.chat_moderar(m.autor, t);
  update public.chat_mensagens set texto = t, editado_em = now() where id = p_id returning * into m;
  return jsonb_build_object('id', m.id, 'texto', m.texto, 'editado_em', m.editado_em);
end $$;

-- Quem desliga a "confirmação de leitura" some da lista de "visto por"
create or replace function public.chat_li_ocultar(p_device text)
returns void language sql security definer set search_path = public as $$
  delete from public.chat_lidos where quem = public.chat_quem(p_device);
$$;

-- Mostrar ou esconder o texto da mensagem nos avisos deste aparelho
create or replace function public.chat_aviso_pref(ep text, p_previa boolean)
returns void language sql security definer set search_path = public as $$
  update public.push_subs set previa = coalesce(p_previa, true) where endpoint = ep;
$$;

revoke all on function public.chat_editar(bigint, text, text) from public;
revoke all on function public.chat_li_ocultar(text)           from public;
revoke all on function public.chat_aviso_pref(text, boolean)  from public;
grant execute on function public.chat_editar(bigint, text, text) to anon, authenticated;
grant execute on function public.chat_li_ocultar(text)           to anon, authenticated;
grant execute on function public.chat_aviso_pref(text, boolean)  to anon, authenticated;

select 'ok: chat jeito Apple pronto' as status;
