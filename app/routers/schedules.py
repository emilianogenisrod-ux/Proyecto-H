from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Doctor, ScheduleBlock
from app.schemas import ScheduleBlockCreate, ScheduleBlockRead, SlotRead
from app.services.availability import generate_available_slots

router = APIRouter(tags=["Horarios"])

WEEKDAY_NAMES = [
    "Lunes",
    "Martes",
    "Miércoles",
    "Jueves",
    "Viernes",
    "Sábado",
    "Domingo",
]


@router.get("/doctors/{doctor_id}/schedules", response_model=list[ScheduleBlockRead])
def list_schedules(doctor_id: int, db: Session = Depends(get_db)):
    doctor = db.get(Doctor, doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor no encontrado")
    return (
        db.query(ScheduleBlock)
        .filter(ScheduleBlock.doctor_id == doctor_id)
        .order_by(ScheduleBlock.weekday, ScheduleBlock.start_time)
        .all()
    )


@router.post("/schedules", response_model=ScheduleBlockRead, status_code=status.HTTP_201_CREATED)
def create_schedule(payload: ScheduleBlockCreate, db: Session = Depends(get_db)):
    if payload.start_time >= payload.end_time:
        raise HTTPException(status_code=400, detail="La hora de inicio debe ser anterior a la de fin")
    doctor = db.get(Doctor, payload.doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor no encontrado")
    block = ScheduleBlock(**payload.model_dump())
    db.add(block)
    db.commit()
    db.refresh(block)
    return block


@router.delete("/schedules/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_schedule(schedule_id: int, db: Session = Depends(get_db)):
    block = db.get(ScheduleBlock, schedule_id)
    if not block:
        raise HTTPException(status_code=404, detail="Horario no encontrado")
    db.delete(block)
    db.commit()


@router.get("/doctors/{doctor_id}/slots", response_model=list[SlotRead])
def list_available_slots(doctor_id: int, day: date, db: Session = Depends(get_db)):
    doctor = db.get(Doctor, doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor no encontrado")
    if not doctor.is_active:
        raise HTTPException(status_code=400, detail="El doctor no está activo")
    slots = generate_available_slots(db, doctor, day)
    return [SlotRead(starts_at=s, ends_at=e) for s, e in slots]
