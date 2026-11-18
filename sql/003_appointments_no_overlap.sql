-- Endurecimiento opcional en PostgreSQL: invariante de no-solape a nivel BD.
-- Requiere extensión btree_gist. No aplica a SQLite local.
CREATE EXTENSION IF NOT EXISTS btree_gist;

ALTER TABLE "hospital-appointments"
  DROP CONSTRAINT IF EXISTS hospital_appointments_no_overlap;

ALTER TABLE "hospital-appointments"
  ADD CONSTRAINT hospital_appointments_no_overlap
  EXCLUDE USING gist (
    doctor_id WITH =,
    tsrange(starts_at, ends_at, '[)') WITH &&
  )
  WHERE (status IN ('scheduled', 'completed', 'no_show'));
