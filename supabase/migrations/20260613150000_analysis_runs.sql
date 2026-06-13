alter type public.analysis_status add value if not exists 'complete';

create type public.analysis_run_status as enum (
  'running',
  'complete',
  'partial',
  'failed'
);

create table public.analysis_runs (
  id uuid primary key default extensions.gen_random_uuid(),
  analysis_id uuid not null references public.analyses(id) on delete cascade,
  owner_id uuid not null references auth.users(id) on delete cascade,
  status public.analysis_run_status not null,
  methodology_version text not null,
  result jsonb,
  error_message text,
  created_at timestamptz not null default timezone('utc', now()),
  completed_at timestamptz,
  constraint analysis_runs_result_is_object
    check (result is null or jsonb_typeof(result) = 'object')
);

create index analysis_runs_analysis_created_idx
  on public.analysis_runs (analysis_id, created_at desc);

alter table public.analysis_runs enable row level security;
revoke all on public.analysis_runs from anon;
grant select, insert, update, delete on public.analysis_runs to authenticated;

create policy "analysis_runs_select_own"
on public.analysis_runs for select
to authenticated
using (
  (select auth.uid()) is not null
  and (select auth.uid()) = owner_id
  and exists (
    select 1 from public.analyses
    where analyses.id = analysis_runs.analysis_id
      and analyses.owner_id = (select auth.uid())
  )
);

create policy "analysis_runs_insert_own"
on public.analysis_runs for insert
to authenticated
with check (
  (select auth.uid()) is not null
  and (select auth.uid()) = owner_id
  and exists (
    select 1 from public.analyses
    where analyses.id = analysis_runs.analysis_id
      and analyses.owner_id = (select auth.uid())
  )
);

create policy "analysis_runs_update_own"
on public.analysis_runs for update
to authenticated
using (
  (select auth.uid()) is not null
  and (select auth.uid()) = owner_id
)
with check (
  (select auth.uid()) is not null
  and (select auth.uid()) = owner_id
);

create policy "analysis_runs_delete_own"
on public.analysis_runs for delete
to authenticated
using (
  (select auth.uid()) is not null
  and (select auth.uid()) = owner_id
);
