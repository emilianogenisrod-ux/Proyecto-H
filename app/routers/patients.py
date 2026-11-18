from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Paciente
from app.schemas import PacienteCreate, PacienteRead, PacienteUpdate

router = APIRouter(prefix="/patients", tags=["Pacientes"])


@router.get("", response_model=list[PacienteRead])
def listar_pacientes(db: Session = Depends(get_db)):
    return db.query(Paciente).order_by(Paciente.nombre_completo).all()


@router.get("/{paciente_id}", response_model=PacienteRead)
def obtener_paciente(paciente_id: int, db: Session = Depends(get_db)):
    paciente = db.get(Paciente, paciente_id)
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    return paciente


@router.post("", response_model=PacienteRead, status_code=status.HTTP_201_CREATED)
def crear_paciente(payload: PacienteCreate, db: Session = Depends(get_db)):
    ya_existe = db.query(Paciente).filter(Paciente.documento == payload.documento).first()
    if ya_existe:
        raise HTTPException(status_code=409, detail="Ese documento ya está registrado")

    paciente = Paciente(**payload.model_dump())
    db.add(paciente)
    db.commit()
    db.refresh(paciente)
    return paciente


@router.put("/{paciente_id}", response_model=PacienteRead)
def actualizar_paciente(paciente_id: int, payload: PacienteUpdate, db: Session = Depends(get_db)):
    paciente = db.get(Paciente, paciente_id)
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")

    cambios = payload.model_dump(exclude_unset=True)
    if "documento" in cambios:
        otro = (
            db.query(Paciente)
            .filter(Paciente.documento == cambios["documento"], Paciente.id != paciente_id)
            .first()
        )
        if otro:
            raise HTTPException(status_code=409, detail="Ese documento ya está registrado")

    for campo, valor in cambios.items():
        setattr(paciente, campo, valor)

    db.commit()
    db.refresh(paciente)
    return paciente


@router.delete("/{paciente_id}", status_code=status.HTTP_204_NO_CONTENT)
def borrar_paciente(paciente_id: int, db: Session = Depends(get_db)):
    paciente = db.get(Paciente, paciente_id)
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    db.delete(paciente)
    db.commit()
