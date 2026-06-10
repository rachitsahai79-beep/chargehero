-- Store charger coordinates as plain latitude/longitude columns.
--
-- The application's ChargerResponse model returns flat `latitude`/`longitude`,
-- but jobs_chargers originally had only a PostGIS `location POINT NOT NULL`.
-- That mismatch made charger reads fail response validation. Add explicit
-- numeric columns the API can read/write directly, and relax the POINT NOT NULL
-- so inserts no longer require it.

ALTER TABLE jobs_chargers ADD COLUMN IF NOT EXISTS latitude  DOUBLE PRECISION;
ALTER TABLE jobs_chargers ADD COLUMN IF NOT EXISTS longitude DOUBLE PRECISION;
ALTER TABLE jobs_chargers ALTER COLUMN location DROP NOT NULL;

-- Backfill lat/lng from any existing POINT values (location is POINT(lng lat)).
UPDATE jobs_chargers
SET latitude  = location[1],
    longitude = location[0]
WHERE location IS NOT NULL AND latitude IS NULL;
