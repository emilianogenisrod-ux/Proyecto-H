from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.especialidades import validar_genero_especialidad
from app.models import BloqueHorario, Cita, Doctor, EstadoCita
from app.schemas import DoctorCreate, DoctorRead, DoctorUpdate
from app.services.availability import bloquear_doctor, horario_disponible, primer_espacio_libre

router = APIRouter(prefix="/doctors", tags=["Doctores"])

ESTADOS_REASIGNABLES = (EstadoCita.programada, EstadoCita.no_asistio, EstadoCita.doctor_ausente)


@router.get("", response_model=list[DoctorRead])
def listar_doctores(active_only: bool = False, db: Session = Depends(get_db)):
    consulta = db.query(Doctor)
    if active_only:
        consulta = consulta.filter(Doctor.activo.is_(True))
    return consulta.order_by(Doctor.nombre_completo).all()


@router.get("/{doctor_id}", response_model=DoctorRead)
def obtener_doctor(doctor_id: int, db: Session = Depends(get_db)):
    doctor = db.get(Doctor, doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor no encontrado")
    return doctor


@router.post("", response_model=DoctorRead, status_code=status.HTTP_201_CREATED)
def crear_doctor(payload: DoctorCreate, db: Session = Depends(get_db)):
    aviso = validar_genero_especialidad(payload.especialidad, sexo_doctor=payload.sexo)
    if aviso:
        raise HTTPException(status_code=400, detail=aviso)
    doctor = Doctor(**payload.model_dump())
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return doctor


@router.put("/{doctor_id}", response_model=DoctorRead)
def actualizar_doctor(doctor_id: int, payload: DoctorUpdate, db: Session = Depends(get_db)):
    doctor = db.get(Doctor, doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor no encontrado")

    cambios = payload.model_dump(exclude_unset=True)
    especialidad = cambios.get("especialidad", doctor.especialidad)
    sexo = cambios.get("sexo", doctor.sexo)
    aviso = validar_genero_especialidad(especialidad, sexo_doctor=sexo)
    if aviso:
        raise HTTPException(status_code=400, detail=aviso)
    for campo, valor in cambios.items():
        setattr(doctor, campo, valor)

    db.commit()
    db.refresh(doctor)
    return doctor


def _doctores_misma_especialidad(db: Session, doctor: Doctor) -> list[Doctor]:
    return (
        db.query(Doctor)
        .filter(
            Doctor.id != doctor.id,
            Doctor.activo.is_(True),
            Doctor.especialidad == doctor.especialidad,
        )
        .order_by(Doctor.nombre_completo)
        .all()
    )


def _asignar_cita_abierta(db: Session, cita: Cita, candidatos: list[Doctor], inicio_rr: int) -> Doctor:
    """Prueba candidatos en round-robin hasta encontrar horario."""
    n = len(candidatos)
    for offset in range(n):
        destino = candidatos[(inicio_rr + offset) % n]
        bloqueado = bloquear_doctor(db, destino.id)
        if not bloqueado or not bloqueado.activo:
            continue
        fin = cita.inicio + timedelta(minutes=bloqueado.minutos_consulta)
        if horario_disponible(db, bloqueado, cita.inicio, fin, excluir_cita_id=cita.id):
            cita.doctor_id = bloqueado.id
            cita.fin = fin
            return bloqueado
        hueco = primer_espacio_libre(db, bloqueado, cita.inicio)
        if hueco:
            cita.inicio, cita.fin = hueco
            cita.doctor_id = bloqueado.id
            return bloqueado
    raise HTTPException(
        status_code=409,
        detail="Ningún doctor de la misma especialidad tiene horario libre para esas citas",
    )


@router.delete("/{doctor_id}", status_code=status.HTTP_204_NO_CONTENT)
def borrar_doctor(
    doctor_id: int,
    redistribuir: bool = Query(False, description="Repartir citas entre doctores de la misma especialidad"),
    doctor_ids: str | None = Query(
        None,
        description="IDs separados por coma; si se omite se usan todos los de la especialidad",
    ),
    # Compatibilidad con el cliente anterior (un solo reemplazo)
    nuevo_doctor_id: int | None = None,
    db: Session = Depends(get_db),
):
    doctor = db.get(Doctor, doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor no encontrado")

    citas = db.query(Cita).filter(Cita.doctor_id == doctor_id).order_by(Cita.inicio).all()
    abiertas = [c for c in citas if c.estado in ESTADOS_REASIGNABLES]
    misma_esp = _doctores_misma_especialidad(db, doctor)

    if citas and not redistribuir and not nuevo_doctor_id:
        raise HTTPException(
            status_code=409,
            detail={
                "mensaje": (
                    f"Este doctor tiene citas. Se repartirán entre otros de "
                    f"{doctor.especialidad} (misma especialidad)."
                ),
                "especialidad": doctor.especialidad,
                "citas": [
                    {
                        "id": c.id,
                        "paciente_id": c.paciente_id,
                        "inicio": c.inicio.isoformat(sep=" "),
                        "estado": c.estado.value,
                    }
                    for c in abiertas
                ],
                "doctores": [
                    {
                        "id": d.id,
                        "nombre_completo": d.nombre_completo,
                        "especialidad": d.especialidad,
                    }
                    for d in misma_esp
                ],
            },
        )

    candidatos: list[Doctor] = []
    if nuevo_doctor_id and not redistribuir and not doctor_ids:
        # Modo legado: un solo doctor (sigue exigiendo misma especialidad)
        if nuevo_doctor_id == doctor_id:
            raise HTTPException(status_code=400, detail="Elige un doctor distinto")
        nuevo = bloquear_doctor(db, nuevo_doctor_id)
        if not nuevo or not nuevo.activo:
            raise HTTPException(status_code=404, detail="El doctor de reemplazo no está disponible")
        if nuevo.especialidad != doctor.especialidad:
            raise HTTPException(
                status_code=400,
                detail="El doctor de reemplazo debe ser de la misma especialidad",
            )
        candidatos = [nuevo]
    elif citas:
        ids_pedidos: list[int] | None = None
        if doctor_ids:
            try:
                ids_pedidos = [int(x.strip()) for x in doctor_ids.split(",") if x.strip()]
            except ValueError as exc:
                raise HTTPException(status_code=400, detail="doctor_ids inválidos") from exc
            if doctor_id in ids_pedidos:
                raise HTTPException(status_code=400, detail="No incluyas al doctor que se elimina")

        pool = misma_esp
        if ids_pedidos is not None:
            ped = set(ids_pedidos)
            pool = [d for d in misma_esp if d.id in ped]
            if len(pool) != len(ped):
                raise HTTPException(
                    status_code=400,
                    detail="Solo se admiten doctores activos de la misma especialidad",
                )

        if not pool:
            raise HTTPException(
                status_code=409,
                detail=f"No hay otros doctores activos de {doctor.especialidad} para repartir las citas",
            )
        candidatos = pool

    if candidatos:
        # Reparto round-robin de citas abiertas
        for i, cita in enumerate(abiertas):
            destino = _asignar_cita_abierta(db, cita, candidatos, i)
            if cita.estado in (EstadoCita.no_asistio, EstadoCita.doctor_ausente):
                cita.estado = EstadoCita.programada
            nota = f"Reasignada a {destino.nombre_completo} al eliminar al doctor anterior"
            cita.notas = f"{cita.notas}. {nota}" if cita.notas else nota

        db.flush()
        # Histórico (completadas/canceladas): también se reparte para no dejar FK huérfana
        resto = [c for c in citas if c.estado not in ESTADOS_REASIGNABLES]
        for i, cita in enumerate(resto):
            destino = candidatos[i % len(candidatos)]
            cita.doctor_id = destino.id

        db.flush()
        colgados = db.query(Cita).filter(Cita.doctor_id == doctor_id).count()
        if colgados:
            raise HTTPException(
                status_code=409,
                detail="Quedaron citas sin reasignar; no se puede eliminar al doctor",
            )

    db.query(BloqueHorario).filter(BloqueHorario.doctor_id == doctor_id).delete(
        synchronize_session=False
    )
    db.query(Doctor).filter(Doctor.id == doctor_id).delete(synchronize_session=False)
    db.commit()
