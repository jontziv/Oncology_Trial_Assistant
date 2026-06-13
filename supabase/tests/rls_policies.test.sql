begin;

select plan(8);

select policies_are(
  'public',
  'profiles',
  array[
    'profiles_delete_own',
    'profiles_insert_own',
    'profiles_select_own',
    'profiles_update_own'
  ]
);

select policies_are(
  'public',
  'analyses',
  array[
    'analyses_delete_own',
    'analyses_insert_own',
    'analyses_select_own',
    'analyses_update_own'
  ]
);

select policy_cmd_is('public', 'analyses', 'analyses_select_own', 'SELECT');
select policy_cmd_is('public', 'analyses', 'analyses_insert_own', 'INSERT');
select policy_cmd_is('public', 'analyses', 'analyses_update_own', 'UPDATE');
select policy_cmd_is('public', 'analyses', 'analyses_delete_own', 'DELETE');
select table_privs_are(
  'anon',
  'public',
  'analyses',
  array[]::text[]
);
select table_privs_are(
  'authenticated',
  'public',
  'analyses',
  array['SELECT', 'INSERT', 'UPDATE', 'DELETE']
);

select * from finish();
rollback;

