create extension if not exists pgcrypto with schema extensions;

create type public.analysis_status as enum ('draft', 'ready');

create table public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  display_name text,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table public.analyses (
  id uuid primary key default extensions.gen_random_uuid(),
  owner_id uuid not null references auth.users(id) on delete cascade,
  title text not null check (char_length(title) between 3 and 200),
  status public.analysis_status not null default 'draft',
  trial jsonb not null,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  constraint analyses_trial_is_object check (jsonb_typeof(trial) = 'object')
);

create index analyses_owner_updated_idx
  on public.analyses (owner_id, updated_at desc);

create function public.set_updated_at()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
begin
  new.updated_at = timezone('utc', now());
  return new;
end;
$$;

create trigger profiles_set_updated_at
before update on public.profiles
for each row execute function public.set_updated_at();

create trigger analyses_set_updated_at
before update on public.analyses
for each row execute function public.set_updated_at();

alter table public.profiles enable row level security;
alter table public.analyses enable row level security;

revoke all on public.profiles from anon;
revoke all on public.analyses from anon;
grant select, insert, update, delete on public.profiles to authenticated;
grant select, insert, update, delete on public.analyses to authenticated;

create policy "profiles_select_own"
on public.profiles for select
to authenticated
using ((select auth.uid()) is not null and (select auth.uid()) = id);

create policy "profiles_insert_own"
on public.profiles for insert
to authenticated
with check ((select auth.uid()) is not null and (select auth.uid()) = id);

create policy "profiles_update_own"
on public.profiles for update
to authenticated
using ((select auth.uid()) is not null and (select auth.uid()) = id)
with check ((select auth.uid()) is not null and (select auth.uid()) = id);

create policy "profiles_delete_own"
on public.profiles for delete
to authenticated
using ((select auth.uid()) is not null and (select auth.uid()) = id);

create policy "analyses_select_own"
on public.analyses for select
to authenticated
using ((select auth.uid()) is not null and (select auth.uid()) = owner_id);

create policy "analyses_insert_own"
on public.analyses for insert
to authenticated
with check ((select auth.uid()) is not null and (select auth.uid()) = owner_id);

create policy "analyses_update_own"
on public.analyses for update
to authenticated
using ((select auth.uid()) is not null and (select auth.uid()) = owner_id)
with check ((select auth.uid()) is not null and (select auth.uid()) = owner_id);

create policy "analyses_delete_own"
on public.analyses for delete
to authenticated
using ((select auth.uid()) is not null and (select auth.uid()) = owner_id);

