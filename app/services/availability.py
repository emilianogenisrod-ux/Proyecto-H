from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.models import BloqueHorario, Cita, Doctor, EstadoCita

# Hora oficial de la agenda (Ciudad de México)
TZ_MEXICO = ZoneInfo("America/Mexico_City")

# Estados que todavía ocupan el horario del doctor
ESTADOS_ACTIVOS = {
    EstadoCita.programada,
    EstadoCita.completada,
    EstadoCita.no_asistio,
}


def ahora_mexico() -> datetime:
    # Naive en hora de México, igual que las citas guardadas en BD
    return datetime.now(TZ_MEXICO).replace(tzinfo=None)


def bloquear_doctor(db: Session, doctor_id: int) -> Doctor | None:
    # Evita que dos reservas al mismo tiempo pasen la validación
    return (
        db.query(Doctor)
        .filter(Doctor.id == doctor_id)
        .with_for_update()
        .first()
    )


def _juntar(dia: date, hora: time) -> datetime:
    return datetime.combine(dia, hora)


def _se_traslapan(a_ini: datetime, a_fin: datetime, b_ini: datetime, b_fin: datetime) -> bool:
    # Dos intervalos se cruzan si cada uno empieza antes de que el otro termine
    return a_ini < b_fin and b_ini < a_fin


def hay_traslape(
    db: Session,
    doctor_id: int,
    inicio: datetime,
    fin: datetime,
    excluir_cita_id: int | None = None,
) -> bool:
    consulta = db.query(Cita).filter(
        Cita.doctor_id == doctor_id,
        Cita.estado.in_(ESTADOS_ACTIVOS),
        Cita.inicio < fin,
        Cita.fin > inicio,
    )
    if excluir_cita_id is not None:
        consulta = consulta.filter(Cita.id != excluir_cita_id)
    return consulta.first() is not None


def generar_espacios_libres(
    db: Session,
    doctor: Doctor,
    dia: date,
    excluir_cita_id: int | None = None,
) -> list[tuple[datetime, datetime]]:
    bloques = (
        db.query(BloqueHorario)
        .filter(BloqueHorario.doctor_id == doctor.id, BloqueHorario.dia_semana == dia.weekday())
        .order_by(BloqueHorario.hora_inicio)
        .all()
    )
    if not bloques:
        return []

    duracion = timedelta(minutes=doctor.minutos_consulta)
    inicio_dia = _juntar(dia, time.min)
    fin_dia = inicio_dia + timedelta(days=1)

    citas_del_dia = db.query(Cita).filter(
        Cita.doctor_id == doctor.id,
        Cita.estado.in_(ESTADOS_ACTIVOS),
        Cita.inicio < fin_dia,
        Cita.fin > inicio_dia,
    )
    if excluir_cita_id is not None:
        citas_del_dia = citas_del_dia.filter(Cita.id != excluir_cita_id)
    citas = citas_del_dia.all()

    ahora = ahora_mexico()
    # Días ya pasados: no hay nada que ofrecer
    if dia < ahora.date():
        return []

    libres: list[tuple[datetime, datetime]] = []
    for bloque in bloques:
        cursor = _juntar(dia, bloque.hora_inicio)
        limite = _juntar(dia, bloque.hora_fin)
        while cursor + duracion <= limite:
            fin_slot = cursor + duracion
            # Solo en el día de hoy se ocultan horas que ya pasaron (hora México)
            if dia == ahora.date() and cursor < ahora:
                cursor = cursor + duracion
                continue
            ocupado = False
            for cita in citas:
                if _se_traslapan(cursor, fin_slot, cita.inicio, cita.fin):
                    ocupado = True
                    break
            if not ocupado:
                libres.append((cursor, fin_slot))
            cursor = cursor + duracion
    return libres


def fecha_agenda_valida(inicio: datetime) -> str | None:
    ahora = ahora_mexico()
    if inicio < ahora:
        return "No se puede agendar una cita en el pasado"
    if inicio > ahora + timedelta(days=365):
        return "Solo se puede agendar hasta 12 meses adelante"
    return None


def primer_espacio_libre(
    db: Session,
    doctor: Doctor,
    desde: datetime,
    dias: int = 45,
) -> tuple[datetime, datetime] | None:
    for offset in range(dias):
        dia = (desde + timedelta(days=offset)).date()
        for ini, fin in generar_espacios_libres(db, doctor, dia):
            if ini >= desde:
                return ini, fin
    return None


def horario_disponible(
    db: Session,
    doctor: Doctor,
    inicio: datetime,
    fin: datetime,
    excluir_cita_id: int | None = None,
) -> bool:
    duracion_esperada = timedelta(minutes=doctor.minutos_consulta)
    if fin - inicio != duracion_esperada:
        return False
    if inicio < ahora_mexico():
        return False

    bloques = (
        db.query(BloqueHorario)
        .filter(
            BloqueHorario.doctor_id == doctor.id,
            BloqueHorario.dia_semana == inicio.date().weekday(),
        )
        .all()
    )

    cae_en_bloque = False
    for bloque in bloques:
        ini_bloque = _juntar(inicio.date(), bloque.hora_inicio)
        fin_bloque = _juntar(inicio.date(), bloque.hora_fin)
        if inicio >= ini_bloque and fin <= fin_bloque:
            cae_en_bloque = True
            break

    if not cae_en_bloque:
        return False

    if hay_traslape(db, doctor.id, inicio, fin, excluir_cita_id):
        return False
    return True


# Nombres viejos por si algún import quedó colgado
lock_doctor_for_scheduling = bloquear_doctor
is_slot_available = horario_disponible
generate_available_slots = generar_espacios_libres
has_conflict = hay_traslape
