#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Prepara datos locales para la revisión en vivo del MVP.

    python seed_test_data.py
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta

from sqlalchemy import delete

from app.database import Base, SessionLocal, engine
from app.models import BloqueHorario, Cita, Doctor, EstadoCita, EstadoPago, Paciente, Pago


def _proximo_lunes() -> date:
    hoy = date.today()
    dias = (0 - hoy.weekday() + 7) % 7
    if dias == 0:
        dias = 7
    return hoy + timedelta(days=dias)


def limpiar_sqlite() -> None:
    if not str(engine.url).startswith("sqlite"):
        raise SystemExit(f"Solo se limpia SQLite local. URL actual: {engine.url}")
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        db.execute(delete(Pago))
        db.execute(delete(Cita))
        db.execute(delete(BloqueHorario))
        db.execute(delete(Paciente))
        db.execute(delete(Doctor))
        db.commit()
    print("OK  Base SQLite limpia.")


def cargar_demo() -> dict:
    lunes = _proximo_lunes()
    inicio = datetime.combine(lunes, time(10, 0))
    fin = inicio + timedelta(minutes=30)

    with SessionLocal() as db:
        perez = Doctor(
            nombre_completo="Dr. Pérez",
            especialidad="Medicina General",
            minutos_consulta=30,
            tarifa=500.0,
            correo="perez@demo.local",
            telefono="555-1001",
            activo=True,
        )
        gomez = Doctor(
            nombre_completo="Dra. Gómez",
            especialidad="Pediatría",
            minutos_consulta=30,
            tarifa=600.0,
            correo="gomez@demo.local",
            telefono="555-1002",
            activo=True,
        )
        db.add_all([perez, gomez])
        db.flush()

        paciente1 = Paciente(
            nombre_completo="Paciente Uno",
            documento="DEMO-P1",
            telefono="555-2001",
            correo="paciente1@demo.local",
        )
        paciente2 = Paciente(
            nombre_completo="Paciente Dos",
            documento="DEMO-P2",
            telefono="555-2002",
            correo="paciente2@demo.local",
        )
        db.add_all([paciente1, paciente2])
        db.flush()

        db.add(
            BloqueHorario(
                doctor_id=perez.id,
                dia_semana=0,
                hora_inicio=time(9, 0),
                hora_fin=time(13, 0),
            )
        )
        db.flush()

        cita = Cita(
            doctor_id=perez.id,
            paciente_id=paciente1.id,
            inicio=inicio,
            fin=fin,
            estado=EstadoCita.programada,
            notas="Cita para la demo",
        )
        db.add(cita)
        db.flush()

        pago = Pago(cita_id=cita.id, monto=perez.tarifa, estado=EstadoPago.pendiente)
        db.add(pago)
        db.commit()

        return {
            "doctor_perez_id": perez.id,
            "doctor_gomez_id": gomez.id,
            "paciente1_id": paciente1.id,
            "paciente2_id": paciente2.id,
            "cita_id": cita.id,
            "pago_id": pago.id,
            "inicio": inicio.isoformat(sep=" "),
            "fin": fin.isoformat(sep=" "),
            "dia_demo": lunes.isoformat(),
        }


def main() -> None:
    limpiar_sqlite()
    info = cargar_demo()
    print("OK  Datos de demo listos.")
    print()
    print("=== IDs para Swagger (http://127.0.0.1:8000/docs) ===")
    for clave, valor in info.items():
        print(f"  {clave}: {valor}")
    print()
    print("Traslape: POST /api/appointments")
    print(
        f'  {{"doctor_id": {info["doctor_perez_id"]}, '
        f'"paciente_id": {info["paciente2_id"]}, '
        f'"inicio": "{info["inicio"].replace(" ", "T")}"}}'
    )
    print(f"Cancelar: POST /api/appointments/{info['cita_id']}/cancel")
    print('  {"motivo": "Paciente no puede asistir"}')


if __name__ == "__main__":
    main()
