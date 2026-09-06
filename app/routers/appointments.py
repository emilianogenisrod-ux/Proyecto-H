from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Appointment, AppointmentStatus, Doctor, Patient, Payment, PaymentStatus
from app.schemas import (
    AppointmentCancel,
    AppointmentCreate,
    AppointmentRead,
    AppointmentReschedule,
    DashboardStats,
)
from app.services.availability import is_slot_available

router = APIRouter(prefix="/appointments", tags=["Citas"])


def _serialize_appointment(appt: Appointment) -> AppointmentRead:
    data = AppointmentRead.model_validate(appt)
    if appt.doctor:
        data.doctor_name = appt.doctor.full_name
    if appt.patient:
        data.patient_name = appt.patient.full_name
        data.patient_document = appt.patient.document_id
    return data


@router.get("/stats/dashboard", response_model=DashboardStats)
def dashboard_stats(db: Session = Depends(get_db)):
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = today_start + timedelta(days=1)
    return DashboardStats(
        doctors_active=db.query(Doctor).filter(Doctor.is_active.is_(True)).count(),
        patients_total=db.query(Patient).count(),
        appointments_today=db.query(Appointment)
        .filter(
            Appointment.starts_at >= today_start,
            Appointment.starts_at < today_end,
            Appointment.status != AppointmentStatus.cancelled,
        )
        .count(),
        payments_pending=db.query(Payment)
        .filter(Payment.status == PaymentStatus.pending)
        .count(),
    )


@router.get("", response_model=list[AppointmentRead])
def list_appointments(
    doctor_id: int | None = None,
    patient_id: int | None = None,
    status_filter: AppointmentStatus | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
):
    query = (
        db.query(Appointment)
        .options(
            joinedload(Appointment.payment),
            joinedload(Appointment.doctor),
            joinedload(Appointment.patient),
        )
        .order_by(Appointment.starts_at.desc())
    )
    if doctor_id:
        query = query.filter(Appointment.doctor_id == doctor_id)
    if patient_id:
        query = query.filter(Appointment.patient_id == patient_id)
    if status_filter:
        query = query.filter(Appointment.status == status_filter)
    return [_serialize_appointment(a) for a in query.all()]


@router.get("/{appointment_id}", response_model=AppointmentRead)
def get_appointment(appointment_id: int, db: Session = Depends(get_db)):
    appt = (
        db.query(Appointment)
        .options(
            joinedload(Appointment.payment),
            joinedload(Appointment.doctor),
            joinedload(Appointment.patient),
        )
        .filter(Appointment.id == appointment_id)
        .first()
    )
    if not appt:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    return _serialize_appointment(appt)


@router.post("", response_model=AppointmentRead, status_code=status.HTTP_201_CREATED)
def create_appointment(payload: AppointmentCreate, db: Session = Depends(get_db)):
    doctor = db.get(Doctor, payload.doctor_id)
    if not doctor or not doctor.is_active:
        raise HTTPException(status_code=404, detail="Doctor no encontrado o inactivo")
    patient = db.get(Patient, payload.patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")

    ends_at = payload.starts_at + timedelta(minutes=doctor.consultation_minutes)
    if not is_slot_available(db, doctor, payload.starts_at, ends_at):
        raise HTTPException(status_code=409, detail="El horario no está disponible o hay solape")

    appt = Appointment(
        doctor_id=payload.doctor_id,
        patient_id=payload.patient_id,
        starts_at=payload.starts_at,
        ends_at=ends_at,
        status=AppointmentStatus.scheduled,
        notes=payload.notes,
    )
    db.add(appt)
    db.flush()

    payment = Payment(
        appointment_id=appt.id,
        amount=doctor.default_fee,
        status=PaymentStatus.pending,
    )
    db.add(payment)
    db.commit()

    appt = (
        db.query(Appointment)
        .options(
            joinedload(Appointment.payment),
            joinedload(Appointment.doctor),
            joinedload(Appointment.patient),
        )
        .filter(Appointment.id == appt.id)
        .first()
    )
    return _serialize_appointment(appt)


@router.post("/{appointment_id}/cancel", response_model=AppointmentRead)
def cancel_appointment(
    appointment_id: int, payload: AppointmentCancel, db: Session = Depends(get_db)
):
    appt = (
        db.query(Appointment)
        .options(joinedload(Appointment.payment), joinedload(Appointment.doctor), joinedload(Appointment.patient))
        .filter(Appointment.id == appointment_id)
        .first()
    )
    if not appt:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    if appt.status == AppointmentStatus.cancelled:
        raise HTTPException(status_code=400, detail="La cita ya está cancelada")

    appt.status = AppointmentStatus.cancelled
    appt.cancellation_reason = payload.reason
    appt.cancelled_at = datetime.utcnow()

    if appt.payment and appt.payment.status == PaymentStatus.paid:
        appt.payment.status = PaymentStatus.refund_pending

    db.commit()
    db.refresh(appt)
    return _serialize_appointment(appt)


@router.post("/{appointment_id}/reschedule", response_model=AppointmentRead)
def reschedule_appointment(
    appointment_id: int, payload: AppointmentReschedule, db: Session = Depends(get_db)
):
    appt = (
        db.query(Appointment)
        .options(joinedload(Appointment.payment), joinedload(Appointment.doctor), joinedload(Appointment.patient))
        .filter(Appointment.id == appointment_id)
        .first()
    )
    if not appt:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    if appt.status == AppointmentStatus.cancelled:
        raise HTTPException(status_code=400, detail="No se puede reprogramar una cita cancelada")

    doctor = db.get(Doctor, appt.doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor no encontrado")

    ends_at = payload.starts_at + timedelta(minutes=doctor.consultation_minutes)
    if not is_slot_available(db, doctor, payload.starts_at, ends_at, exclude_appointment_id=appt.id):
        raise HTTPException(status_code=409, detail="El nuevo horario no está disponible")

    appt.starts_at = payload.starts_at
    appt.ends_at = ends_at
    if appt.status == AppointmentStatus.no_show:
        appt.status = AppointmentStatus.scheduled

    db.commit()
    db.refresh(appt)
    return _serialize_appointment(appt)
