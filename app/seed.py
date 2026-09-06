from datetime import datetime, time, timedelta

from sqlalchemy.orm import Session

from app.models import (
    Appointment,
    AppointmentStatus,
    Doctor,
    Patient,
    Payment,
    PaymentStatus,
    ScheduleBlock,
)


def seed_if_empty(db: Session) -> None:
    if db.query(Doctor).count() > 0:
        return

    doctors_data = [
        {
            "full_name": "Dra. Ana Martínez",
            "specialty": "Cardiología",
            "consultation_minutes": 30,
            "default_fee": 800.0,
        },
        {
            "full_name": "Dr. Luis Herrera",
            "specialty": "Pediatría",
            "consultation_minutes": 25,
            "default_fee": 600.0,
        },
        {
            "full_name": "Dra. Carmen Ruiz",
            "specialty": "Medicina General",
            "consultation_minutes": 20,
            "default_fee": 450.0,
        },
    ]

    doctors: list[Doctor] = []
    for data in doctors_data:
        doctor = Doctor(**data, is_active=True)
        db.add(doctor)
        doctors.append(doctor)
    db.flush()

    for doctor in doctors:
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

    patients_data = [
        {
            "full_name": "María González",
            "document_id": "DOC-001",
            "phone": "555-0101",
            "email": "maria@email.com",
        },
        {
            "full_name": "Carlos Pérez",
            "document_id": "DOC-002",
            "phone": "555-0102",
            "email": "carlos@email.com",
        },
        {
            "full_name": "Laura Sánchez",
            "document_id": "DOC-003",
            "phone": "555-0103",
            "email": "laura@email.com",
        },
        {
            "full_name": "Roberto Díaz",
            "document_id": "DOC-004",
            "phone": "555-0104",
            "email": "roberto@email.com",
        },
    ]

    patients: list[Patient] = []
    for data in patients_data:
        patient = Patient(**data)
        db.add(patient)
        patients.append(patient)
    db.flush()

    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    next_monday = today + timedelta(days=(7 - today.weekday()) % 7 or 7)
    next_monday = next_monday.replace(hour=9, minute=0)

    appt1_start = next_monday
    appt1_end = appt1_start + timedelta(minutes=doctors[0].consultation_minutes)
    appt1 = Appointment(
        doctor_id=doctors[0].id,
        patient_id=patients[0].id,
        starts_at=appt1_start,
        ends_at=appt1_end,
        status=AppointmentStatus.scheduled,
        notes="Control cardíaco",
    )
    db.add(appt1)
    db.flush()
    db.add(
        Payment(
            appointment_id=appt1.id,
            amount=doctors[0].default_fee,
            status=PaymentStatus.paid,
            method="card",
            paid_at=datetime.utcnow(),
        )
    )

    appt2_start = next_monday.replace(hour=10, minute=0)
    appt2_end = appt2_start + timedelta(minutes=doctors[1].consultation_minutes)
    appt2 = Appointment(
        doctor_id=doctors[1].id,
        patient_id=patients[1].id,
        starts_at=appt2_start,
        ends_at=appt2_end,
        status=AppointmentStatus.scheduled,
        notes="Revisión pediátrica",
    )
    db.add(appt2)
    db.flush()
    db.add(
        Payment(
            appointment_id=appt2.id,
            amount=doctors[1].default_fee,
            status=PaymentStatus.pending,
        )
    )

    appt3_start = next_monday.replace(hour=15, minute=0)
    appt3_end = appt3_start + timedelta(minutes=doctors[2].consultation_minutes)
    appt3 = Appointment(
        doctor_id=doctors[2].id,
        patient_id=patients[2].id,
        starts_at=appt3_start,
        ends_at=appt3_end,
        status=AppointmentStatus.scheduled,
        notes="Consulta general",
    )
    db.add(appt3)
    db.flush()
    db.add(
        Payment(
            appointment_id=appt3.id,
            amount=doctors[2].default_fee,
            status=PaymentStatus.exempt,
            notes="Paciente con convenio",
        )
    )

    db.commit()
