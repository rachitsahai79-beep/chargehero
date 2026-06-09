-- Corrective migration: align auth_engineer_registrations with application code.
--
-- Migration 001 created this table in a normalized form (auth_user_id, first_name,
-- last_name, registration_status, ...). The application code instead treats it as a
-- flat onboarding record with columns: phone, email, name, dob, status.
-- That mismatch caused registration inserts/queries to fail with HTTP 500.
--
-- Nothing in the schema has a FOREIGN KEY to auth_engineer_registrations
-- (verified across migrations 002-005), so it is safe to drop and recreate.
-- DROP ... CASCADE also removes the old trigger, indexes, and RLS policies.

DROP TABLE IF EXISTS auth_engineer_registrations CASCADE;

CREATE TABLE auth_engineer_registrations (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phone       VARCHAR(20) NOT NULL,
    email       VARCHAR(255),
    name        VARCHAR(255),
    dob         DATE,
    status      VARCHAR(50) NOT NULL DEFAULT 'phone_verified',
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_auth_engineer_registrations_phone  ON auth_engineer_registrations(phone);
CREATE INDEX idx_auth_engineer_registrations_status ON auth_engineer_registrations(status);

-- Reuse the updated_at trigger function created in migration 001.
CREATE TRIGGER auth_engineer_registrations_updated_at
    BEFORE UPDATE ON auth_engineer_registrations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Enable RLS. The backend connects with the service-role key (which bypasses RLS),
-- so backend reads/writes work. With no policies defined, all access via the public
-- anon/publishable key is denied by default -- the most secure baseline.
-- NOTE: if you later switch the backend's anon client to a true anon key, add
-- explicit INSERT/SELECT policies here (or route these writes through the service
-- client) so registration continues to work.
ALTER TABLE auth_engineer_registrations ENABLE ROW LEVEL SECURITY;
