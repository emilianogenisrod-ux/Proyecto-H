from datetime import time

from fastapi import Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.models import BloqueHorario, Doctor, Paciente
from app.security import verify_password
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


def _extras_usuario(db: Session, registro: dict) -> dict:
    extras: dict = {}
    if registro["role"] == ROLE_DOCTOR:
        doctor = db.query(Doctor).filter(Doctor.correo == registro["email"]).first()
        if doctor:
            extras["doctor_id"] = doctor.id
            extras["specialty"] = doctor.especialidad
    elif registro["role"] == ROLE_PATIENT:
        paciente = db.query(Paciente).filter(Paciente.correo == registro["email"]).first()
        if paciente:
            extras["patient_id"] = paciente.id
            extras["document_id"] = paciente.documento
    return extras


def authenticate(email: str, password: str, db: Session | None = None) -> dict | None:
    email_n = (email or "").strip().lower()
    registro = USERS.get(email_n)
    esperado = password_for(email_n)
    if not registro or not esperado or not verify_password(password, esperado):
        return None
    extras = _extras_usuario(db, registro) if db is not None else {}
    return public_user(registro, extras)


def ensure_role_entities(db: Session) -> None:
    doctor_user = USERS["doctor@farma"]
    doctor = db.query(Doctor).filter(Doctor.correo == doctor_user["email"]).first()
    if not doctor:
        doctor = Doctor(
            nombre_completo=doctor_user["name"],
            especialidad=doctor_user.get("specialty", "Medicina General"),
            minutos_consulta=30,
            tarifa=500.0,
            correo=doctor_user["email"],
            telefono="555-0800",
            activo=True,
        )
        db.add(doctor)
        db.flush()
        for dia in range(5):
            for h_ini, h_fin in [(9, 13), (15, 18)]:
                db.add(
                    BloqueHorario(
                        doctor_id=doctor.id,
                        dia_semana=dia,
                        hora_inicio=time(h_ini, 0),
                        hora_fin=time(h_fin, 0),
                    )
                )
    else:
        doctor.nombre_completo = doctor_user["name"]
        doctor.especialidad = doctor_user.get("specialty", doctor.especialidad)
        doctor.activo = True

    patient_user = USERS["paciente@farma"]
    paciente = db.query(Paciente).filter(Paciente.correo == patient_user["email"]).first()
    if not paciente:
        por_documento = (
            db.query(Paciente).filter(Paciente.documento == patient_user["document_id"]).first()
        )
        if por_documento:
            por_documento.correo = patient_user["email"]
            por_documento.nombre_completo = patient_user["name"]
            por_documento.telefono = patient_user.get("phone")
        else:
            db.add(
                Paciente(
                    nombre_completo=patient_user["name"],
                    documento=patient_user["document_id"],
                    telefono=patient_user.get("phone"),
                    correo=patient_user["email"],
                )
            )
    else:
        paciente.nombre_completo = patient_user["name"]
        paciente.telefono = patient_user.get("phone")

    db.commit()
