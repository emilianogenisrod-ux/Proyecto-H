from datetime import date, datetime, time, timedelta

from sqlalchemy.orm import Session

from app.models import Appointment, AppointmentStatus, Doctor, ScheduleBlock


ACTIVE_STATUSES = {
    AppointmentStatus.scheduled,
    AppointmentStatus.completed,
    AppointmentStatus.no_show,
}


def _combine(day: date, t: time) -> datetime:
    return datetime.combine(day, t)


def _overlaps(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    return a_start < b_end and b_start < a_end


def get_doctor_appointments_for_day(
    db: Session, doctor_id: int, day: date, exclude_appointment_id: int | None = None
) -> list[Appointment]:
    day_start = _combine(day, time.min)
    day_end = day_start + timedelta(days=1)
    query = db.query(Appointment).filter(
        Appointment.doctor_id == doctor_id,
        Appointment.status.in_(ACTIVE_STATUSES),
        Appointment.starts_at < day_end,
        Appointment.ends_at > day_start,
    )
    if exclude_appointment_id:
        query = query.filter(Appointment.id != exclude_appointment_id)
    return query.all()


def has_conflict(
    db: Session,
    doctor_id: int,
    starts_at: datetime,
    ends_at: datetime,
    exclude_appointment_id: int | None = None,
) -> bool:
    query = db.query(Appointment).filter(
        Appointment.doctor_id == doctor_id,
        Appointment.status.in_(ACTIVE_STATUSES),
        Appointment.starts_at < ends_at,
        Appointment.ends_at > starts_at,
    )
    if exclude_appointment_id:
        query = query.filter(Appointment.id != exclude_appointment_id)
    return query.first() is not None


def generate_available_slots(
    db: Session,
    doctor: Doctor,
    day: date,
    exclude_appointment_id: int | None = None,
) -> list[tuple[datetime, datetime]]:
    weekday = day.weekday()
    blocks = (
        db.query(ScheduleBlock)
        .filter(ScheduleBlock.doctor_id == doctor.id, ScheduleBlock.weekday == weekday)
        .order_by(ScheduleBlock.start_time)
        .all()
    )
    if not blocks:
        return []

    duration = timedelta(minutes=doctor.consultation_minutes)
    appointments = get_doctor_appointments_for_day(db, doctor.id, day, exclude_appointment_id)
    slots: list[tuple[datetime, datetime]] = []

    for block in blocks:
        cursor = _combine(day, block.start_time)
        block_end = _combine(day, block.end_time)
        while cursor + duration <= block_end:
            slot_end = cursor + duration
            conflict = any(
                _overlaps(cursor, slot_end, appt.starts_at, appt.ends_at) for appt in appointments
            )
            if not conflict:
                slots.append((cursor, slot_end))
            cursor += duration

    return slots


def is_slot_available(
    db: Session,
    doctor: Doctor,
    starts_at: datetime,
    ends_at: datetime,
    exclude_appointment_id: int | None = None,
) -> bool:
    day = starts_at.date()
    expected_duration = timedelta(minutes=doctor.consultation_minutes)
    if ends_at - starts_at != expected_duration:
        return False

    weekday = day.weekday()
    blocks = db.query(ScheduleBlock).filter(
        ScheduleBlock.doctor_id == doctor.id, ScheduleBlock.weekday == weekday
    ).all()

    in_block = False
    for block in blocks:
        block_start = _combine(day, block.start_time)
        block_end = _combine(day, block.end_time)
        if starts_at >= block_start and ends_at <= block_end:
            in_block = True
            break
    if not in_block:
        return False

    return not has_conflict(db, doctor.id, starts_at, ends_at, exclude_appointment_id)
