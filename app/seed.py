from datetime import datetime, time, timedelta

from sqlalchemy.orm import Session

from app.models import BloqueHorario, Cita, Doctor, EstadoCita, EstadoPago, Paciente, Pago


def seed_if_empty(db: Session) -> None:
    if db.query(Doctor).count() > 0:
        return

    doctores = [
        Doctor(
            nombre_completo="Dra. Ana Martínez",
            especialidad="Dermatología",
            minutos_consulta=30,
            tarifa=800.0,
            activo=True,
        ),
        Doctor(
            nombre_completo="Dr. Luis Herrera",
            especialidad="Pediatría",
            minutos_consulta=30,
            tarifa=600.0,
            activo=True,
        ),
        Doctor(
            nombre_completo="Dra. Carmen Ruiz",
            especialidad="Medicina General",
            minutos_consulta=30,
            tarifa=450.0,
            activo=True,
        ),
        Doctor(
            nombre_completo="Dra. Sofía Reyes",
            especialidad="Ginecología",
            minutos_consulta=30,
            tarifa=700.0,
            activo=True,
        ),
    ]
    for doctor in doctores:
        db.add(doctor)
    db.flush()

    for doctor in doctores:
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

    pacientes = [
        Paciente(
            nombre_completo="María González",
            documento="DOC-001",
            telefono="555-0101",
            correo="maria@email.com",
        ),
        Paciente(
            nombre_completo="Carlos Pérez",
            documento="DOC-002",
            telefono="555-0102",
            correo="carlos@email.com",
        ),
        Paciente(
            nombre_completo="Laura Sánchez",
            documento="DOC-003",
            telefono="555-0103",
            correo="laura@email.com",
        ),
        Paciente(
            nombre_completo="Roberto Díaz",
            documento="DOC-004",
            telefono="555-0104",
            correo="roberto@email.com",
        ),
    ]
    for paciente in pacientes:
        db.add(paciente)
    db.flush()

    hoy = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    lunes = hoy + timedelta(days=(7 - hoy.weekday()) % 7 or 7)

    cita1_inicio = lunes.replace(hour=9, minute=0)
    cita1 = Cita(
        doctor_id=doctores[0].id,
        paciente_id=pacientes[0].id,
        inicio=cita1_inicio,
        fin=cita1_inicio + timedelta(minutes=doctores[0].minutos_consulta),
        estado=EstadoCita.programada,
        notas="Control cardíaco",
    )
    db.add(cita1)
    db.flush()
    db.add(
        Pago(
            cita_id=cita1.id,
            monto=doctores[0].tarifa,
            estado=EstadoPago.pagado,
            metodo="card",
            fecha_pago=datetime.utcnow(),
        )
    )

    cita2_inicio = lunes.replace(hour=10, minute=0)
    cita2 = Cita(
        doctor_id=doctores[1].id,
        paciente_id=pacientes[1].id,
        inicio=cita2_inicio,
        fin=cita2_inicio + timedelta(minutes=doctores[1].minutos_consulta),
        estado=EstadoCita.programada,
        notas="Revisión pediátrica",
    )
    db.add(cita2)
    db.flush()
    db.add(
        Pago(
            cita_id=cita2.id,
            monto=doctores[1].tarifa,
            estado=EstadoPago.pendiente,
        )
    )

    cita3_inicio = lunes.replace(hour=15, minute=0)
    cita3 = Cita(
        doctor_id=doctores[2].id,
        paciente_id=pacientes[2].id,
        inicio=cita3_inicio,
        fin=cita3_inicio + timedelta(minutes=doctores[2].minutos_consulta),
        estado=EstadoCita.programada,
        notas="Consulta general",
    )
    db.add(cita3)
    db.flush()
    db.add(
        Pago(
            cita_id=cita3.id,
            monto=doctores[2].tarifa,
            estado=EstadoPago.exento,
            notas="Paciente con convenio",
        )
    )

    db.commit()
