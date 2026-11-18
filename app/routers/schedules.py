from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import BloqueHorario, Doctor
from app.schemas import BloqueHorarioCreate, BloqueHorarioRead, EspacioLibre
from app.services.availability import generar_espacios_libres
from app.services.schedule_gen import generar_horarios_aleatorios

router = APIRouter(tags=["Horarios"])


class GenerarHorariosRequest(BaseModel):
    reemplazar: bool = Field(
        default=False,
        description="Si ya hay horarios, bórralos y genera de nuevo",
    )


@router.get("/doctors/{doctor_id}/schedules", response_model=list[BloqueHorarioRead])
def listar_horarios(doctor_id: int, db: Session = Depends(get_db)):
    doctor = db.get(Doctor, doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor no encontrado")
    return (
        db.query(BloqueHorario)
        .filter(BloqueHorario.doctor_id == doctor_id)
        .order_by(BloqueHorario.dia_semana, BloqueHorario.hora_inicio)
        .all()
    )


@router.post("/schedules", response_model=BloqueHorarioRead, status_code=status.HTTP_201_CREATED)
def crear_horario(payload: BloqueHorarioCreate, db: Session = Depends(get_db)):
    if payload.hora_inicio >= payload.hora_fin:
        raise HTTPException(status_code=400, detail="La hora de inicio debe ser antes que la de fin")

    doctor = db.get(Doctor, payload.doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor no encontrado")

    bloque = BloqueHorario(**payload.model_dump())
    db.add(bloque)
    db.commit()
    db.refresh(bloque)
    return bloque


@router.delete("/schedules/{horario_id}", status_code=status.HTTP_204_NO_CONTENT)
def borrar_horario(horario_id: int, db: Session = Depends(get_db)):
    bloque = db.get(BloqueHorario, horario_id)
    if not bloque:
        raise HTTPException(status_code=404, detail="Horario no encontrado")
    db.delete(bloque)
    db.commit()


@router.post(
    "/doctors/{doctor_id}/schedules/generate",
    response_model=list[BloqueHorarioRead],
    status_code=status.HTTP_201_CREATED,
)
def generar_horarios_doctor(
    doctor_id: int,
    payload: GenerarHorariosRequest | None = None,
    db: Session = Depends(get_db),
):
    doctor = db.get(Doctor, doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor no encontrado")
    reemplazar = payload.reemplazar if payload else False
    try:
        return generar_horarios_aleatorios(db, doctor, reemplazar=reemplazar)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/doctors/{doctor_id}/slots", response_model=list[EspacioLibre])
def listar_espacios_libres(
    doctor_id: int,
    day: date,
    excluir_cita_id: int | None = None,
    db: Session = Depends(get_db),
):
    doctor = db.get(Doctor, doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor no encontrado")
    if not doctor.activo:
        raise HTTPException(status_code=400, detail="El doctor no está activo")

    espacios = generar_espacios_libres(db, doctor, day, excluir_cita_id=excluir_cita_id)
    return [EspacioLibre(inicio=ini, fin=fin) for ini, fin in espacios]
