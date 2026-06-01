-- Bootstrap: create the app role used by RLS policies
-- This runs once on first container start via docker-entrypoint-initdb.d

-- The application connects as forense_app (superuser created by POSTGRES_USER env).
-- We create a restricted role app_user that the audit_log REVOKE targets.
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_user') THEN
    CREATE ROLE app_user;
  END IF;
END
$$;

-- Grant app_user to forense_app so the REVOKE in migrations is valid
GRANT app_user TO forense_app;
