from fastapi import Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import time

from app.models import Doctor, Patient, ScheduleBlock
from app.users import ROLE_DOCTOR, ROLE_HOME, ROLE_PATIENT, USERS, password_for, public_user

SESSION_USER_KEY = "user"


def get_session_user(request: Request) -> dict | None:
    return request.session.get(SESSION_USER_KEY)


def home_for_user(user: dict | None) -> str:
    if not user:
        return "/login"
    return user.get("home") or ROLE_HOME.get(user.get("role"), "/login")


def require_login(request: Request) -> dict | RedirectResponse:
    user = get_session_user(request)
    if user:
        return user
    return RedirectResponse(url="/login", status_code=303)


def require_roles(request: Request, *roles: str) -> dict | RedirectResponse:
    user = get_session_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    if user.get("role") not in roles:
        return RedirectResponse(url=home_for_user(user), status_code=303)
    return user


def _resolve_extras(db: Session, record: dict) -> dict:
    extras: dict = {}
    if record["role"] == ROLE_DOCTOR:
        doctor = db.query(Doctor).filter(Doctor.email == record["email"]).first()
        if doctor:
            extras["doctor_id"] = doctor.id
            extras["specialty"] = doctor.specialty
    elif record["role"] == ROLE_PATIENT:
        patient = db.query(Patient).filter(Patient.email == record["email"]).first()
        if patient:
            extras["patient_id"] = patient.id
            extras["document_id"] = patient.document_id
    return extras


def authenticate(email: str, password: str, db: Session | None = None) -> dict | None:
    email_n = (email or "").strip().lower()
    record = USERS.get(email_n)
    expected = password_for(email_n)
    if not record or not expected or expected != password:
        return None
    extras = _resolve_extras(db, record) if db is not None else {}
    return public_user(record, extras)


def ensure_role_entities(db: Session) -> None:
    """Garantiza doctor y paciente vinculados a las cuentas demo."""
    doctor_user = USERS["doctor@farma"]
    doctor = db.query(Doctor).filter(Doctor.email == doctor_user["email"]).first()
    if not doctor:
        doctor = Doctor(
            full_name=doctor_user["name"],
            specialty=doctor_user.get("specialty", "Medicina General"),
            consultation_minutes=30,
            default_fee=500.0,
            email=doctor_user["email"],
            phone="555-0800",
            is_active=True,
        )
        db.add(doctor)
        db.flush()
        for weekday in range(5):
            for start_h, end_h in [(9, 13), (15, 18)]:
                db.add(
                    ScheduleBlock(
                        doctor_id=doctor.id,
                        weekday=weekday,
                        start_time=time(start_h, 0),
                        end_time=time(end_h, 0),
                    )
                )
    else:
        doctor.full_name = doctor_user["name"]
        doctor.specialty = doctor_user.get("specialty", doctor.specialty)
        doctor.is_active = True

    patient_user = USERS["paciente@farma"]
    patient = db.query(Patient).filter(Patient.email == patient_user["email"]).first()
    if not patient:
        existing_doc = (
            db.query(Patient).filter(Patient.document_id == patient_user["document_id"]).first()
        )
        if existing_doc:
            existing_doc.email = patient_user["email"]
            existing_doc.full_name = patient_user["name"]
            existing_doc.phone = patient_user.get("phone")
        else:
            db.add(
                Patient(
                    full_name=patient_user["name"],
                    document_id=patient_user["document_id"],
                    phone=patient_user.get("phone"),
                    email=patient_user["email"],
                )
            )
    else:
        patient.full_name = patient_user["name"]
        patient.phone = patient_user.get("phone")

    db.commit()
