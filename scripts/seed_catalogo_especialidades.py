#!/usr/bin/env python
"""Catálogo demo: 2 doctores y 2 pacientes por especialidad, horarios sin traslape.

Uso (en el contenedor o local con .env):
    PYTHONPATH=/app python scripts/seed_catalogo_especialidades.py
"""

from __future__ import annotations

from datetime import time

from app.database import SessionLocal, init_db
from app.especialidades import ESPECIALIDADES
from app.models import BloqueHorario, Doctor, Paciente

# 2 doctor(a)s por especialidad. Ginecología: solo mujeres.
DOCTORES = [
    ("Dra. Elena Vargas", "Medicina General", "F", "elena.vargas@hospital.local", 450.0),
    ("Dr. Marcos Díaz", "Medicina General", "M", "marcos.diaz@hospital.local", 450.0),
    ("Dra. Lucía Paredes", "Pediatría", "F", "lucia.paredes@hospital.local", 550.0),
    ("Dr. Iván Soto", "Pediatría", "M", "ivan.soto@hospital.local", 550.0),
    ("Dra. Camila Ríos", "Ginecología", "F", "camila.rios@hospital.local", 700.0),
    ("Dra. Valeria Núñez", "Ginecología", "F", "valeria.nunez@hospital.local", 700.0),
    ("Dra. Paula Mendoza", "Dermatología", "F", "paula.mendoza@hospital.local", 650.0),
    ("Dr. Héctor Salinas", "Dermatología", "M", "hector.salinas@hospital.local", 650.0),
]

# 2 pacientes por especialidad (etiqueta en documento). Ginecología: solo mujeres.
PACIENTES = [
    ("Ana López García", "MG-F-001", "F", "Medicina General"),
    ("Luis Torres Ruiz", "MG-M-001", "M", "Medicina General"),
    ("Sofía Ramírez Peña", "PED-F-001", "F", "Pediatría"),
    ("Diego Herrera Cruz", "PED-M-001", "M", "Pediatría"),
    ("Mariana Castillo", "GIN-F-001", "F", "Ginecología"),
    ("Andrea Fuentes", "GIN-F-002", "F", "Ginecología"),
    ("Carla Ortega", "DER-F-001", "F", "Dermatología"),
    ("Pedro Aguilar", "DER-M-001", "M", "Dermatología"),
]

# 8 franjas exclusivas (90 min) → un doctor por franja, sin traslape
FRANJAS = [
    (time(8, 0), time(9, 30)),
    (time(9, 30), time(11, 0)),
    (time(11, 0), time(12, 30)),
    (time(12, 30), time(14, 0)),
    (time(14, 0), time(15, 30)),
    (time(15, 30), time(17, 0)),
    (time(17, 0), time(18, 30)),
    (time(18, 30), time(20, 0)),
]


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


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        correos_ok = {c[3] for c in DOCTORES}
        doctores: list[Doctor] = []
        for row in DOCTORES:
            doctores.append(_upsert_doctor(db, *row))
        db.flush()

        # Solo el catálogo queda activo (2 por especialidad)
        for d in db.query(Doctor).all():
            if (d.correo or "") not in correos_ok:
                d.activo = False
        db.flush()

        for nombre, docu, sexo, _esp in PACIENTES:
            _upsert_paciente(db, nombre, docu, sexo)
        db.flush()

        # Reconstruir horarios solo del catálogo, sin traslapes el mismo día
        ids = [d.id for d in doctores]
        db.query(BloqueHorario).filter(BloqueHorario.doctor_id.in_(ids)).delete(
            synchronize_session=False
        )
        db.flush()

        # Cada día laboral: cada doctor una franja distinta (rota por día)
        for dia in range(5):  # lun-vie
            for i, doctor in enumerate(doctores):
                franja = FRANJAS[(i + dia) % len(FRANJAS)]
                db.add(
                    BloqueHorario(
                        doctor_id=doctor.id,
                        dia_semana=dia,
                        hora_inicio=franja[0],
                        hora_fin=franja[1],
                    )
                )

        db.commit()
        print("OK catálogo especialidades")
        for esp in ESPECIALIDADES:
            docs = [d for d in doctores if d.especialidad == esp]
            print(f"  {esp}: {len(docs)} doctores -> " + ", ".join(d.nombre_completo for d in docs))
        print(f"  pacientes catálogo: {len(PACIENTES)}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
