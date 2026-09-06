"""Datos estructurados para la vista de documentación del sistema."""

from __future__ import annotations

from sqlalchemy.schema import CreateTable

from app.database import Base, engine


def get_create_table_sql() -> list[dict[str, str]]:
    from app import models  # noqa: F401

    statements: list[dict[str, str]] = []
    for table in Base.metadata.sorted_tables:
        ddl = str(CreateTable(table).compile(dialect=engine.dialect))
        statements.append({"name": table.name, "sql": ddl.strip() + ";"})
    return statements


API_ENDPOINTS = [
    {"method": "GET", "path": "/api/doctors", "desc": "Listar doctores", "auth": "Sesión"},
    {"method": "GET", "path": "/api/doctors/{id}", "desc": "Obtener doctor", "auth": "Sesión"},
    {"method": "POST", "path": "/api/doctors", "desc": "Crear doctor", "auth": "Sesión"},
    {"method": "PUT", "path": "/api/doctors/{id}", "desc": "Actualizar doctor", "auth": "Sesión"},
    {"method": "DELETE", "path": "/api/doctors/{id}", "desc": "Eliminar doctor", "auth": "Sesión"},
    {"method": "GET", "path": "/api/patients", "desc": "Listar pacientes", "auth": "Sesión"},
    {"method": "GET", "path": "/api/patients/{id}", "desc": "Obtener paciente", "auth": "Sesión"},
    {"method": "POST", "path": "/api/patients", "desc": "Crear paciente", "auth": "Sesión"},
    {"method": "PUT", "path": "/api/patients/{id}", "desc": "Actualizar paciente", "auth": "Sesión"},
    {"method": "DELETE", "path": "/api/patients/{id}", "desc": "Eliminar paciente", "auth": "Sesión"},
    {"method": "GET", "path": "/api/doctors/{id}/schedules", "desc": "Horarios del doctor", "auth": "Sesión"},
    {"method": "POST", "path": "/api/schedules", "desc": "Crear bloque horario", "auth": "Sesión"},
    {"method": "DELETE", "path": "/api/schedules/{id}", "desc": "Eliminar horario", "auth": "Sesión"},
    {"method": "GET", "path": "/api/doctors/{id}/slots?day=YYYY-MM-DD", "desc": "Slots disponibles", "auth": "Sesión"},
    {"method": "GET", "path": "/api/appointments", "desc": "Listar citas (filtros doctor_id, patient_id, status)", "auth": "Sesión"},
    {"method": "GET", "path": "/api/appointments/stats/dashboard", "desc": "KPIs del dashboard", "auth": "Sesión"},
    {"method": "GET", "path": "/api/appointments/{id}", "desc": "Detalle de cita", "auth": "Sesión"},
    {"method": "POST", "path": "/api/appointments", "desc": "Agendar cita (+ pago pending)", "auth": "Sesión"},
    {"method": "POST", "path": "/api/appointments/{id}/cancel", "desc": "Cancelar cita", "auth": "Sesión"},
    {"method": "POST", "path": "/api/appointments/{id}/reschedule", "desc": "Reprogramar cita", "auth": "Sesión"},
    {"method": "GET", "path": "/api/payments", "desc": "Listar pagos", "auth": "Sesión"},
    {"method": "GET", "path": "/api/payments/{id}", "desc": "Detalle de pago", "auth": "Sesión"},
    {"method": "PATCH", "path": "/api/payments/{id}", "desc": "Actualizar estado de pago", "auth": "Sesión"},
    {"method": "GET", "path": "/api/media", "desc": "Listar medios", "auth": "Sesión"},
    {"method": "POST", "path": "/api/media/upload", "desc": "Subir imagen/video (multipart)", "auth": "Sesión"},
    {"method": "DELETE", "path": "/api/media/{id}", "desc": "Eliminar medio", "auth": "Sesión"},
    {"method": "GET", "path": "/api/me", "desc": "Usuario de la sesión actual", "auth": "Sesión"},
    {"method": "POST", "path": "/login", "desc": "Autenticación (form email/password)", "auth": "Público"},
    {"method": "GET", "path": "/logout", "desc": "Cerrar sesión", "auth": "Sesión"},
]

TABLES_DOC = [
    {
        "name": "hospital-doctors",
        "purpose": "Profesionales de la salud y tarifas.",
        "select": 'SELECT id, full_name, specialty, consultation_minutes, default_fee, phone, email, is_active, created_at FROM "hospital-doctors";',
        "orm": "db.query(Doctor).filter(Doctor.is_active.is_(True)).all()",
    },
    {
        "name": "hospital-patients",
        "purpose": "Expediente básico de pacientes.",
        "select": 'SELECT id, full_name, document_id, phone, email, created_at FROM "hospital-patients";',
        "orm": "db.query(Patient).filter(Patient.document_id == doc).first()",
    },
    {
        "name": "hospital-schedule_blocks",
        "purpose": "Bloques semanales de disponibilidad por doctor.",
        "select": 'SELECT id, doctor_id, weekday, start_time, end_time FROM "hospital-schedule_blocks" WHERE doctor_id = $1;',
        "orm": "db.query(ScheduleBlock).filter(ScheduleBlock.doctor_id == doctor_id).all()",
    },
    {
        "name": "hospital-appointments",
        "purpose": "Citas médicas (estados, cancelación, reprogramación).",
        "select": 'SELECT id, doctor_id, patient_id, starts_at, ends_at, status, notes FROM "hospital-appointments" WHERE status = \'scheduled\';',
        "orm": "db.query(Appointment).options(joinedload(Appointment.payment)).all()",
    },
    {
        "name": "hospital-payments",
        "purpose": "Cobros 1:1 asociados a cada cita.",
        "select": 'SELECT id, appointment_id, amount, status, method, paid_at FROM "hospital-payments";',
        "orm": "db.query(Payment).filter(Payment.status == PaymentStatus.pending).all()",
    },
    {
        "name": "hospital-media_assets",
        "purpose": "Metadatos de imágenes/videos/plantillas (archivos en MinIO).",
        "select": 'SELECT id, title, kind, filename, folder, storage_key, storage_url, size_bytes, uploaded_by FROM "hospital-media_assets";',
        "orm": "db.query(MediaAsset).order_by(MediaAsset.created_at.desc()).all()",
    },
]
