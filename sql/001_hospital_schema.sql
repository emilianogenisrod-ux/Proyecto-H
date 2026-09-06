-- Proyecto H · esquema hospitalario en Supabase (PostgreSQL)
-- Nomenclatura: hospital-<tabla>

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

DO $$ BEGIN
  CREATE TYPE hospital_appointment_status AS ENUM (
    'scheduled', 'completed', 'cancelled', 'no_show'
  );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE TYPE hospital_payment_status AS ENUM (
    'pending', 'paid', 'partial', 'exempt', 'refund_pending'
  );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE TYPE hospital_media_kind AS ENUM ('image', 'video', 'template');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS "hospital-doctors" (
  id SERIAL PRIMARY KEY,
  full_name VARCHAR(200) NOT NULL,
  specialty VARCHAR(120) NOT NULL,
  consultation_minutes INTEGER NOT NULL DEFAULT 30,
  default_fee DOUBLE PRECISION NOT NULL DEFAULT 500.0,
  phone VARCHAR(30),
  email VARCHAR(120),
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_hospital_doctors_email ON "hospital-doctors" (email);

CREATE TABLE IF NOT EXISTS "hospital-patients" (
  id SERIAL PRIMARY KEY,
  full_name VARCHAR(200) NOT NULL,
  document_id VARCHAR(50) NOT NULL UNIQUE,
  phone VARCHAR(30),
  email VARCHAR(120),
  created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_hospital_patients_document ON "hospital-patients" (document_id);

CREATE TABLE IF NOT EXISTS "hospital-schedule_blocks" (
  id SERIAL PRIMARY KEY,
  doctor_id INTEGER NOT NULL REFERENCES "hospital-doctors"(id) ON DELETE CASCADE,
  weekday INTEGER NOT NULL CHECK (weekday BETWEEN 0 AND 6),
  start_time TIME NOT NULL,
  end_time TIME NOT NULL,
  CONSTRAINT uq_hospital_schedule UNIQUE (doctor_id, weekday, start_time, end_time)
);

CREATE TABLE IF NOT EXISTS "hospital-appointments" (
  id SERIAL PRIMARY KEY,
  doctor_id INTEGER NOT NULL REFERENCES "hospital-doctors"(id),
  patient_id INTEGER NOT NULL REFERENCES "hospital-patients"(id),
  starts_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
  ends_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
  status hospital_appointment_status NOT NULL DEFAULT 'scheduled',
  notes VARCHAR(500),
  cancellation_reason VARCHAR(500),
  cancelled_at TIMESTAMP WITHOUT TIME ZONE,
  created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_hospital_appointments_starts ON "hospital-appointments" (starts_at);
CREATE INDEX IF NOT EXISTS idx_hospital_appointments_doctor ON "hospital-appointments" (doctor_id);
CREATE INDEX IF NOT EXISTS idx_hospital_appointments_patient ON "hospital-appointments" (patient_id);

CREATE TABLE IF NOT EXISTS "hospital-payments" (
  id SERIAL PRIMARY KEY,
  appointment_id INTEGER NOT NULL UNIQUE REFERENCES "hospital-appointments"(id) ON DELETE CASCADE,
  amount DOUBLE PRECISION NOT NULL,
  status hospital_payment_status NOT NULL DEFAULT 'pending',
  method VARCHAR(30),
  paid_at TIMESTAMP WITHOUT TIME ZONE,
  notes VARCHAR(500),
  created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS "hospital-media_assets" (
  id SERIAL PRIMARY KEY,
  title VARCHAR(200) NOT NULL,
  kind hospital_media_kind NOT NULL,
  filename VARCHAR(255) NOT NULL,
  original_name VARCHAR(255) NOT NULL,
  content_type VARCHAR(120) NOT NULL,
  size_bytes INTEGER NOT NULL DEFAULT 0,
  folder VARCHAR(40) NOT NULL DEFAULT 'images',
  storage_key VARCHAR(500),
  storage_url VARCHAR(800),
  bucket VARCHAR(120) DEFAULT 'hospital',
  uploaded_by VARCHAR(120),
  created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_hospital_media_kind ON "hospital-media_assets" (kind);
CREATE INDEX IF NOT EXISTS idx_hospital_media_uploaded_by ON "hospital-media_assets" (uploaded_by);

COMMENT ON TABLE "hospital-doctors" IS 'Profesionales de la salud · Proyecto H';
COMMENT ON TABLE "hospital-patients" IS 'Pacientes · Proyecto H';
COMMENT ON TABLE "hospital-schedule_blocks" IS 'Bloques de horario semanal · Proyecto H';
COMMENT ON TABLE "hospital-appointments" IS 'Citas médicas · Proyecto H';
COMMENT ON TABLE "hospital-payments" IS 'Pagos asociados a citas · Proyecto H';
COMMENT ON TABLE "hospital-media_assets" IS 'Metadatos de medios en MinIO · Proyecto H';
