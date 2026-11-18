"""Genera bloques de horario lógicos para un doctor.

Prefiere turnos que no se traslapen con otros doctores; si el hospital
ya está lleno, igual asigna el turno con menos choques para no fallar.
"""

from __future__ import annotations

import random
from datetime import time

from sqlalchemy.orm import Session

from app.models import BloqueHorario, Doctor

# Turnos típicos (mañana / mediodía / tarde), con variedad para repartir carga
TURNOS = [
    (time(7, 0), time(11, 0)),
    (time(8, 0), time(12, 0)),
    (time(9, 0), time(13, 0)),
    (time(10, 0), time(14, 0)),
    (time(11, 0), time(15, 0)),
    (time(13, 0), time(17, 0)),
    (time(14, 0), time(18, 0)),
    (time(15, 0), time(19, 0)),
    (time(16, 0), time(20, 0)),
    (time(8, 0), time(14, 0)),
    (time(14, 0), time(20, 0)),
]

DIAS_LABORABLES = [0, 1, 2, 3, 4]  # lun-vie


def _se_traslapan(a_ini: time, a_fin: time, b_ini: time, b_fin: time) -> bool:
    return a_ini < b_fin and b_ini < a_fin


def _bloques_ocupados_otros(db: Session, excepto_doctor_id: int) -> list[BloqueHorario]:
    return (
        db.query(BloqueHorario)
        .join(Doctor, Doctor.id == BloqueHorario.doctor_id)
        .filter(BloqueHorario.doctor_id != excepto_doctor_id, Doctor.activo.is_(True))
        .all()
    )


def _cubre_consulta(ini: time, fin: time, minutos: int) -> bool:
    total = (fin.hour * 60 + fin.minute) - (ini.hour * 60 + ini.minute)
    return total >= max(minutos * 2, 60)


def _contar_choques(
    dia: int,
    ini: time,
    fin: time,
    ocupados: list[BloqueHorario],
) -> int:
    return sum(
        1
        for b in ocupados
        if b.dia_semana == dia and _se_traslapan(ini, fin, b.hora_inicio, b.hora_fin)
    )


def _elegir_turno(
    dia: int,
    minutos: int,
    ocupados: list[BloqueHorario],
    ya_elegidos: list[tuple[time, time]],
) -> tuple[time, time] | None:
    puntuados: list[tuple[int, time, time]] = []
    for ini, fin in TURNOS:
        if not _cubre_consulta(ini, fin, minutos):
            continue
        if any(_se_traslapan(ini, fin, e_ini, e_fin) for e_ini, e_fin in ya_elegidos):
            continue
        choques = _contar_choques(dia, ini, fin, ocupados)
        puntuados.append((choques, ini, fin))
    if not puntuados:
        return None
    # Primero los de menos choques; entre empates, al azar
    mejor = min(puntuados, key=lambda x: x[0])[0]
    finalistas = [(ini, fin) for choques, ini, fin in puntuados if choques == mejor]
    return random.choice(finalistas)


def generar_horarios_aleatorios(
    db: Session,
    doctor: Doctor,
    reemplazar: bool = False,
) -> list[BloqueHorario]:
    """Arma una semana laboral; evita choques cuando se puede, nunca deja vacío."""
    existentes = (
        db.query(BloqueHorario).filter(BloqueHorario.doctor_id == doctor.id).count()
    )
    if existentes and not reemplazar:
        raise ValueError("El doctor ya tiene horarios. Usa reemplazar=true para regenerarlos.")

    if reemplazar and existentes:
        db.query(BloqueHorario).filter(BloqueHorario.doctor_id == doctor.id).delete(
            synchronize_session=False
        )
        db.flush()

    ocupados = _bloques_ocupados_otros(db, doctor.id)
    minutos = doctor.minutos_consulta or 30

    cuantos_dias = random.randint(4, 5)
    dias = sorted(random.sample(DIAS_LABORABLES, cuantos_dias))

    mananas = [t for t in TURNOS if t[0] < time(12, 0)]
    tardes = [t for t in TURNOS if t[0] >= time(13, 0)]

    creados: list[BloqueHorario] = []
    for dia in dias:
        elegidos: list[tuple[time, time]] = []

        # Siempre intenta un turno de mañana (para poder agendar p. ej. a las 10)
        manana_opts = [
            (ini, fin)
            for ini, fin in mananas
            if _cubre_consulta(ini, fin, minutos)
        ]
        if manana_opts:
            # Prefiere el de menos choques
            manana_opts.sort(key=lambda t: _contar_choques(dia, t[0], t[1], ocupados))
            mejores_m = [t for t in manana_opts if _contar_choques(dia, t[0], t[1], ocupados) == _contar_choques(dia, manana_opts[0][0], manana_opts[0][1], ocupados)]
            elegidos.append(random.choice(mejores_m))

        # Y casi siempre uno de tarde
        if random.random() < 0.85:
            tarde = _elegir_turno(dia, minutos, ocupados, elegidos)
            # Fuerza preferencia vespertina si el elegido fue otra mañana
            if tarde and tarde[0] < time(13, 0):
                tarde_opts = [
                    (ini, fin)
                    for ini, fin in tardes
                    if _cubre_consulta(ini, fin, minutos)
                    and not any(_se_traslapan(ini, fin, e[0], e[1]) for e in elegidos)
                ]
                if tarde_opts:
                    tarde_opts.sort(key=lambda t: _contar_choques(dia, t[0], t[1], ocupados))
                    tarde = tarde_opts[0]
            if tarde:
                elegidos.append(tarde)

        if not elegidos:
            backup = _elegir_turno(dia, minutos, ocupados, [])
            if backup:
                elegidos.append(backup)

        for ini, fin in elegidos:
            bloque = BloqueHorario(
                doctor_id=doctor.id,
                dia_semana=dia,
                hora_inicio=ini,
                hora_fin=fin,
            )
            db.add(bloque)
            creados.append(bloque)

    # Garantía: si por alguna razón no hubo nada, plantilla fija lun–vie mañana
    if not creados:
        for dia in DIAS_LABORABLES:
            bloque = BloqueHorario(
                doctor_id=doctor.id,
                dia_semana=dia,
                hora_inicio=time(9, 0),
                hora_fin=time(13, 0),
            )
            db.add(bloque)
            creados.append(bloque)

    db.commit()
    for bloque in creados:
        db.refresh(bloque)
    return creados
