-- Run once in your own Supabase project's SQL editor.
-- The public SDK key is safe only with these database access rules.
begin;
create table public.review_events (
  id uuid primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  notebook_id text not null check (length(notebook_id) between 1 and 512),
  rating text not null check (rating in ('again','shaky','good','easy')),
  review_day date not null,
  recorded_at timestamptz not null default clock_timestamp()
);
create index review_events_user_order on public.review_events(user_id, recorded_at, id);
alter table public.review_events enable row level security;
revoke all on public.review_events from anon, authenticated;
grant select, delete on public.review_events to authenticated;
grant insert (id, user_id, notebook_id, rating, review_day) on public.review_events to authenticated;
create policy "Read own reviews" on public.review_events for select to authenticated
  using ((select auth.uid()) = user_id);
create policy "Record own reviews" on public.review_events for insert to authenticated
  with check ((select auth.uid()) = user_id);
create policy "Delete own reviews" on public.review_events for delete to authenticated
  using ((select auth.uid()) = user_id);
-- No UPDATE policy or grant: existing events cannot be replaced.
commit;
