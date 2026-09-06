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
    {"method": "GET", "path": "/api/doctors", "desc": "Ver la lista de doctores", "auth": "Sí (sesión)"},
    {"method": "GET", "path": "/api/doctors/{id}", "desc": "Ver un doctor en concreto", "auth": "Sí (sesión)"},
    {"method": "POST", "path": "/api/doctors", "desc": "Registrar un doctor nuevo", "auth": "Sí (sesión)"},
    {"method": "PUT", "path": "/api/doctors/{id}", "desc": "Actualizar datos de un doctor", "auth": "Sí (sesión)"},
    {"method": "DELETE", "path": "/api/doctors/{id}", "desc": "Eliminar un doctor", "auth": "Sí (sesión)"},
    {"method": "GET", "path": "/api/patients", "desc": "Ver la lista de pacientes", "auth": "Sí (sesión)"},
    {"method": "GET", "path": "/api/patients/{id}", "desc": "Ver un paciente en concreto", "auth": "Sí (sesión)"},
    {"method": "POST", "path": "/api/patients", "desc": "Registrar un paciente nuevo", "auth": "Sí (sesión)"},
    {"method": "PUT", "path": "/api/patients/{id}", "desc": "Actualizar datos de un paciente", "auth": "Sí (sesión)"},
    {"method": "DELETE", "path": "/api/patients/{id}", "desc": "Eliminar un paciente", "auth": "Sí (sesión)"},
    {"method": "GET", "path": "/api/doctors/{id}/schedules", "desc": "Ver horarios de un doctor", "auth": "Sí (sesión)"},
    {"method": "POST", "path": "/api/schedules", "desc": "Crear un bloque de horario", "auth": "Sí (sesión)"},
    {"method": "DELETE", "path": "/api/schedules/{id}", "desc": "Borrar un horario", "auth": "Sí (sesión)"},
    {"method": "GET", "path": "/api/doctors/{id}/slots?day=YYYY-MM-DD", "desc": "Ver horas libres de un día", "auth": "Sí (sesión)"},
    {"method": "GET", "path": "/api/appointments", "desc": "Ver citas (se puede filtrar)", "auth": "Sí (sesión)"},
    {"method": "GET", "path": "/api/appointments/stats/dashboard", "desc": "Ver números resumen del panel", "auth": "Sí (sesión)"},
    {"method": "GET", "path": "/api/appointments/{id}", "desc": "Ver detalle de una cita", "auth": "Sí (sesión)"},
    {"method": "POST", "path": "/api/appointments", "desc": "Agendar una cita nueva", "auth": "Sí (sesión)"},
    {"method": "POST", "path": "/api/appointments/{id}/cancel", "desc": "Cancelar una cita", "auth": "Sí (sesión)"},
    {"method": "POST", "path": "/api/appointments/{id}/reschedule", "desc": "Cambiar la hora de una cita", "auth": "Sí (sesión)"},
    {"method": "GET", "path": "/api/payments", "desc": "Ver pagos", "auth": "Sí (sesión)"},
    {"method": "GET", "path": "/api/payments/{id}", "desc": "Ver un pago", "auth": "Sí (sesión)"},
    {"method": "PATCH", "path": "/api/payments/{id}", "desc": "Cambiar el estado de un pago", "auth": "Sí (sesión)"},
    {"method": "GET", "path": "/api/media", "desc": "Ver archivos subidos", "auth": "Sí (sesión)"},
    {"method": "POST", "path": "/api/media/upload", "desc": "Subir una imagen/video/plantilla", "auth": "Sí (sesión)"},
    {"method": "DELETE", "path": "/api/media/{id}", "desc": "Borrar un archivo", "auth": "Sí (sesión)"},
    {"method": "GET", "path": "/api/me", "desc": "Ver quién soy en esta sesión", "auth": "Sí (sesión)"},
    {"method": "POST", "path": "/login", "desc": "Iniciar sesión", "auth": "No (público)"},
    {"method": "GET", "path": "/logout", "desc": "Cerrar sesión", "auth": "Sí (sesión)"},
]

TABLES_DOC = [
    {
        "name": "hospital-doctors",
        "purpose": "Lista de doctores: nombre, especialidad, duración de consulta y tarifa.",
        "select": 'SELECT id, full_name, specialty, consultation_minutes, default_fee, phone, email, is_active, created_at FROM "hospital-doctors";',
        "orm": "db.query(Doctor).filter(Doctor.is_active.is_(True)).all()",
    },
    {
        "name": "hospital-patients",
        "purpose": "Lista de pacientes: nombre, documento, teléfono y correo.",
        "select": 'SELECT id, full_name, document_id, phone, email, created_at FROM "hospital-patients";',
        "orm": "db.query(Patient).filter(Patient.document_id == doc).first()",
    },
    {
        "name": "hospital-schedule_blocks",
        "purpose": "Horarios semanales de cada doctor (día, hora de inicio y fin).",
        "select": 'SELECT id, doctor_id, weekday, start_time, end_time FROM "hospital-schedule_blocks" WHERE doctor_id = $1;',
        "orm": "db.query(ScheduleBlock).filter(ScheduleBlock.doctor_id == doctor_id).all()",
    },
    {
        "name": "hospital-appointments",
        "purpose": "Citas médicas: quién, con quién, cuándo y en qué estado está.",
        "select": 'SELECT id, doctor_id, patient_id, starts_at, ends_at, status, notes FROM "hospital-appointments" WHERE status = \'scheduled\';',
        "orm": "db.query(Appointment).options(joinedload(Appointment.payment)).all()",
    },
    {
        "name": "hospital-payments",
        "purpose": "Cobros de cada cita (pendiente, pagado, parcial, etc.).",
        "select": 'SELECT id, appointment_id, amount, status, method, paid_at FROM "hospital-payments";',
        "orm": "db.query(Payment).filter(Payment.status == PaymentStatus.pending).all()",
    },
    {
        "name": "hospital-media_assets",
        "purpose": "Ficha de fotos/videos/plantillas (el archivo real está en la bodega MinIO).",
        "select": 'SELECT id, title, kind, filename, folder, storage_key, storage_url, size_bytes, uploaded_by FROM "hospital-media_assets";',
        "orm": "db.query(MediaAsset).order_by(MediaAsset.created_at.desc()).all()",
    },
]
