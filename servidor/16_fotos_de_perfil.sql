-- Fervor · 16 · Fotos de perfil (corrige "new row violates row-level security policy")
-- Cole no SQL Editor do Supabase e clique em Run. Pode rodar mais de uma vez.
--
-- Cada pessoa envia a foto para a própria pasta (o nome da pasta é o id do login).
-- A liderança (administradores) pode enviar para qualquer pasta.

insert into storage.buckets (id, name, public, file_size_limit)
values ('perfis', 'perfis', true, 5242880)
on conflict (id) do update set public = true, file_size_limit = 5242880;

drop policy if exists "b6 perfis ler"     on storage.objects;
drop policy if exists "b6 perfis enviar"  on storage.objects;
drop policy if exists "b6 perfis alterar" on storage.objects;
drop policy if exists "b6 perfis apagar"  on storage.objects;

create policy "b6 perfis ler" on storage.objects for select
  using (bucket_id = 'perfis');

create policy "b6 perfis enviar" on storage.objects for insert to authenticated
  with check (bucket_id = 'perfis' and ((storage.foldername(name))[1] = auth.uid()::text or public.is_admin()));

create policy "b6 perfis alterar" on storage.objects for update to authenticated
  using (bucket_id = 'perfis' and ((storage.foldername(name))[1] = auth.uid()::text or public.is_admin()))
  with check (bucket_id = 'perfis' and ((storage.foldername(name))[1] = auth.uid()::text or public.is_admin()));

create policy "b6 perfis apagar" on storage.objects for delete to authenticated
  using (bucket_id = 'perfis' and ((storage.foldername(name))[1] = auth.uid()::text or public.is_admin()));
