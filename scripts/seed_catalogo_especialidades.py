#!/usr/bin/env python
"""Catálogo demo: doctores/pacientes por especialidad + pocas citas coherentes.

Uso:
    PYTHONPATH=/app python scripts/seed_catalogo_especialidades.py
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, time

from app.database import SessionLocal, init_db
from app.especialidades import ESPECIALIDADES
from app.models import BloqueHorario, Cita, Doctor, EstadoCita, EstadoPago, Paciente, Pago
from app.services.availability import generar_espacios_libres

# 4 doctor(a)s por especialidad. Ginecología: solo mujeres.
DOCTORES = [
    ("Dra. Elena Vargas", "Medicina General", "F", "elena.vargas@hospital.local", 450.0),
    ("Dr. Marcos Díaz", "Medicina General", "M", "marcos.diaz@hospital.local", 450.0),
    ("Dra. Nora Jiménez", "Medicina General", "F", "nora.jimenez@hospital.local", 460.0),
    ("Dr. Raúl Benítez", "Medicina General", "M", "raul.benitez@hospital.local", 460.0),
    ("Dra. Lucía Paredes", "Pediatría", "F", "lucia.paredes@hospital.local", 550.0),
    ("Dr. Iván Soto", "Pediatría", "M", "ivan.soto@hospital.local", 550.0),
    ("Dra. Brenda Quintero", "Pediatría", "F", "brenda.quintero@hospital.local", 560.0),
    ("Dr. Tomás Galván", "Pediatría", "M", "tomas.galvan@hospital.local", 560.0),
    ("Dra. Camila Ríos", "Ginecología", "F", "camila.rios@hospital.local", 700.0),
    ("Dra. Valeria Núñez", "Ginecología", "F", "valeria.nunez@hospital.local", 700.0),
    ("Dra. Irene Solís", "Ginecología", "F", "irene.solis@hospital.local", 720.0),
    ("Dra. Patricia Leyva", "Ginecología", "F", "patricia.leyva@hospital.local", 720.0),
    ("Dra. Paula Mendoza", "Dermatología", "F", "paula.mendoza@hospital.local", 650.0),
    ("Dr. Héctor Salinas", "Dermatología", "M", "hector.salinas@hospital.local", 650.0),
    ("Dra. Gina Robles", "Dermatología", "F", "gina.robles@hospital.local", 670.0),
    ("Dr. Omar Trejo", "Dermatología", "M", "omar.trejo@hospital.local", 670.0),
]

# 4 pacientes por especialidad (documento → especialidad de atención).
PACIENTES = [
    ("Ana López García", "MG-F-001", "F", "Medicina General"),
    ("Luis Torres Ruiz", "MG-M-001", "M", "Medicina General"),
    ("Fernanda Mejía", "MG-F-002", "F", "Medicina General"),
    ("Jorge Palacios", "MG-M-002", "M", "Medicina General"),
    ("Sofía Ramírez Peña", "PED-F-001", "F", "Pediatría"),
    ("Diego Herrera Cruz", "PED-M-001", "M", "Pediatría"),
    ("Camila Duarte", "PED-F-002", "F", "Pediatría"),
    ("Emilio Vargas", "PED-M-002", "M", "Pediatría"),
    ("Mariana Castillo", "GIN-F-001", "F", "Ginecología"),
    ("Andrea Fuentes", "GIN-F-002", "F", "Ginecología"),
    ("Laura Espinosa", "GIN-F-003", "F", "Ginecología"),
    ("Daniela Mora", "GIN-F-004", "F", "Ginecología"),
    ("Carla Ortega", "DER-F-001", "F", "Dermatología"),
    ("Pedro Aguilar", "DER-M-001", "M", "Dermatología"),
    ("Rebeca Silva", "DER-F-002", "F", "Dermatología"),
    ("Mauricio Peña", "DER-M-002", "M", "Dermatología"),
]

NOTAS = {
    "Medicina General": "Consulta de control",
    "Pediatría": "Revisión pediátrica",
    "Ginecología": "Control ginecológico",
    "Dermatología": "Revisión dermatológica",
}


def _franjas_exclusivas(n: int, minutos: int = 45) -> list[tuple[time, time]]:
    base = datetime.combine(date.today(), time(8, 0))
    out: list[tuple[time, time]] = []
    for i in range(n):
        ini = base + timedelta(minutes=minutos * i)
        fin = ini + timedelta(minutes=minutos)
        out.append((ini.time(), fin.time()))
    return out


def _proximo_dia_laboral(desde: date, weekday: int) -> date:
    delta = (weekday - desde.weekday()) % 7
    if delta == 0:
        delta = 7
    return desde + timedelta(days=delta)


def _upsert_doctor(db, nombre, especialidad, sexo, correo, tarifa) -> Doctor:
    doc = db.query(Doctor).filter(Doctor.correo == correo).first()
    if not doc:
        doc = Doctor(correo=correo)
        db.add(doc)
    doc.nombre_completo = nombre
    doc.especialidad = especialidad
    doc.sexo = sexo
    doc.minutos_consulta = 30
    doc.tarifa = tarifa
    doc.activo = True
    doc.telefono = "555-0100"
    return doc


def _upsert_paciente(db, nombre, documento, sexo) -> Paciente:
    p = db.query(Paciente).filter(Paciente.documento == documento).first()
    if not p:
        p = Paciente(documento=documento)
        db.add(p)
    p.nombre_completo = nombre
    p.sexo = sexo
    p.telefono = "555-0200"
    p.correo = f"{documento.lower()}@paciente.local"
    return p


def _limpiar_citas_demo(db) -> int:
    """Quita citas/pagos previos para dejar un historial corto y coherente."""
    pagos = db.query(Pago).delete(synchronize_session=False)
    citas = db.query(Cita).delete(synchronize_session=False)
    db.flush()
    return citas + pagos


def _agendar_una(
    db,
    doctor: Doctor,
    paciente: Paciente,
    dia: date,
    nota: str,
) -> Cita | None:
    slots = generar_espacios_libres(db, doctor, dia)
    if not slots:
        return None
    inicio, fin = slots[0]
    cita = Cita(
        doctor_id=doctor.id,
        paciente_id=paciente.id,
        inicio=inicio,
        fin=fin,
        estado=EstadoCita.programada,
        notas=nota,
    )
    db.add(cita)
    db.flush()
    db.add(
        Pago(
            cita_id=cita.id,
            monto=doctor.tarifa,
            estado=EstadoPago.pendiente,
        )
    )
    return cita


def _sembrar_citas(db, doctores: list[Doctor], pacientes_esp: list[tuple[Paciente, str]]) -> int:
    """Una sola cita programada por paciente, con doctor de su especialidad."""
    por_esp: dict[str, list[Doctor]] = {}
    for d in doctores:
        por_esp.setdefault(d.especialidad, []).append(d)

    hoy = date.today()
    creadas = 0
    contador_esp: dict[str, int] = {e: 0 for e in ESPECIALIDADES}

    for paciente, especialidad in pacientes_esp:
        grupo = por_esp.get(especialidad) or []
        if not grupo:
            continue
        idx = contador_esp[especialidad]
        doctor = grupo[idx % len(grupo)]
        # Reparte en días laborales distintos para no saturar un mismo día
        weekday = idx % 5  # lun-vie
        dia = _proximo_dia_laboral(hoy, weekday)
        # Si cae hoy y la franja ya pasó, usa la semana siguiente
        if dia == hoy:
            dia = hoy + timedelta(days=7)

        cita = _agendar_una(db, doctor, paciente, dia, NOTAS.get(especialidad, "Consulta"))
        if not cita:
            # Prueba otros días laborales
            for w in range(5):
                alt = _proximo_dia_laboral(hoy + timedelta(days=1), w)
                cita = _agendar_una(
                    db, doctor, paciente, alt, NOTAS.get(especialidad, "Consulta")
                )
                if cita:
                    break
        if cita:
            creadas += 1
        contador_esp[especialidad] = idx + 1

    return creadas


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        correos_ok = {c[3] for c in DOCTORES}
        doctores: list[Doctor] = []
        for row in DOCTORES:
            doctores.append(_upsert_doctor(db, *row))
        db.flush()

        for d in db.query(Doctor).all():
            if (d.correo or "") not in correos_ok:
                d.activo = False
        db.flush()

        pacientes_esp: list[tuple[Paciente, str]] = []
        for nombre, docu, sexo, esp in PACIENTES:
            pacientes_esp.append((_upsert_paciente(db, nombre, docu, sexo), esp))
        db.flush()

        borrados = _limpiar_citas_demo(db)

        ids = [d.id for d in doctores]
        db.query(BloqueHorario).filter(BloqueHorario.doctor_id.in_(ids)).delete(
            synchronize_session=False
        )
        db.flush()

        franjas = _franjas_exclusivas(len(doctores), minutos=45)
        for dia in range(5):
            for i, doctor in enumerate(doctores):
                franja = franjas[(i + dia) % len(franjas)]
                db.add(
                    BloqueHorario(
                        doctor_id=doctor.id,
                        dia_semana=dia,
                        hora_inicio=franja[0],
                        hora_fin=franja[1],
                    )
                )
        db.flush()

        creadas = _sembrar_citas(db, doctores, pacientes_esp)
        db.commit()

        print("OK catálogo especialidades")
        for esp in ESPECIALIDADES:
            docs = [d for d in doctores if d.especialidad == esp]
            print(f"  {esp}: {len(docs)} doctores -> " + ", ".join(d.nombre_completo for d in docs))
        print(f"  pacientes catálogo: {len(PACIENTES)}")
        print(f"  citas previas borradas (filas pago+cita): {borrados}")
        print(f"  citas nuevas (1 por paciente): {creadas}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
