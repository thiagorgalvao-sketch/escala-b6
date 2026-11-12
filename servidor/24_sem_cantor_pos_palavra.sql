-- 24_sem_cantor_pos_palavra.sql
-- Remove o cantor principal das músicas marcadas como "Pós-Palavra" em todos os cultos.
-- Pode rodar mais de uma vez sem problema. Guarda uma cópia de segurança antes de mudar.
do $fv$
declare
 t text; r record; d jsonb; ct text; ut text; wj text; wu text; sid text; n int:=0;
begin
 foreach t in array array['team','pub'] loop
  execute format('create table if not exists public.%I as table public.%I','bkp_'||t||'_20261112b',t);
  select data_type into ct from information_schema.columns where table_schema='public' and table_name=t and column_name='j';
  select data_type into ut from information_schema.columns where table_schema='public' and table_name=t and column_name='u';
  wj := case when ct='jsonb' then 'to_jsonb($2::text)' when ct='json' then 'to_json($2::text)' else '$2' end;
  wu := case when ut like 'timestamp%' then 'now()' else '(extract(epoch from clock_timestamp())*1000)::bigint' end;
  for r in execute format('select id, to_jsonb(j) as j from public.%I where id like $1',t) using 'l_%' loop
   d := r.j; if jsonb_typeof(d)='string' then d := (d #>> '{}')::jsonb; end if;
   if jsonb_typeof(d->'ord')<>'object' or jsonb_typeof(d->'cant')<>'object' then continue; end if;
   for sid in select key from jsonb_each_text(d->'ord') where value='Pós-Palavra' loop
    if (d->'cant') ? sid then d := jsonb_set(d,'{cant}',(d->'cant') - sid); n := n+1; end if;
   end loop;
   execute format('update public.%I set j=%s,u=%s where id=$1',t,wj,wu) using r.id, d::text;
  end loop;
 end loop;
 raise notice 'Pronto: % cantores removidos do Pós-Palavra (somando as duas tabelas).',n;
end $fv$;
select 'ok: sem cantor principal no Pós-Palavra' as status;
