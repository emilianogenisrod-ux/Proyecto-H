from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.especialidades import validar_genero_especialidad
from app.models import BloqueHorario, Cita, Doctor, EstadoCita
from app.schemas import DoctorCreate, DoctorRead, DoctorUpdate
from app.services.availability import bloquear_doctor, horario_disponible, primer_espacio_libre

router = APIRouter(prefix="/doctors", tags=["Doctores"])


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


@router.delete("/{doctor_id}", status_code=status.HTTP_204_NO_CONTENT)
def borrar_doctor(
    doctor_id: int,
    nuevo_doctor_id: int | None = None,
    db: Session = Depends(get_db),
):
    doctor = db.get(Doctor, doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor no encontrado")

    citas = db.query(Cita).filter(Cita.doctor_id == doctor_id).all()
    abiertas = [c for c in citas if c.estado in (EstadoCita.programada, EstadoCita.no_asistio)]

    if citas and not nuevo_doctor_id:
        otros = (
            db.query(Doctor)
            .filter(Doctor.id != doctor_id, Doctor.activo.is_(True))
            .order_by(Doctor.nombre_completo)
            .all()
        )
        raise HTTPException(
            status_code=409,
            detail={
                "mensaje": "Este doctor tiene citas. Elige otro doctor para reasignarlas.",
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
                    {"id": d.id, "nombre_completo": d.nombre_completo} for d in otros
                ],
            },
        )

    if nuevo_doctor_id:
        if nuevo_doctor_id == doctor_id:
            raise HTTPException(status_code=400, detail="Elige un doctor distinto")

        nuevo = bloquear_doctor(db, nuevo_doctor_id)
        if not nuevo or not nuevo.activo:
            raise HTTPException(
                status_code=404,
                detail="El doctor de reemplazo no está disponible",
            )

        for cita in abiertas:
            fin = cita.inicio + timedelta(minutes=nuevo.minutos_consulta)
            if horario_disponible(db, nuevo, cita.inicio, fin, excluir_cita_id=cita.id):
                cita.doctor_id = nuevo.id
                cita.fin = fin
            else:
                hueco = primer_espacio_libre(db, nuevo, cita.inicio)
                if not hueco:
                    raise HTTPException(
                        status_code=409,
                        detail="El doctor elegido no tiene horario libre para esas citas",
                    )
                cita.inicio, cita.fin = hueco
                cita.doctor_id = nuevo.id
            if cita.estado == EstadoCita.no_asistio:
                cita.estado = EstadoCita.programada
            nota = "Reasignada al eliminar al doctor anterior"
            cita.notas = f"{cita.notas}. {nota}" if cita.notas else nota

        # El resto de citas (canceladas/completadas) también se pasan
        db.flush()
        db.query(Cita).filter(Cita.doctor_id == doctor_id).update(
            {Cita.doctor_id: nuevo.id},
            synchronize_session=False,
        )

    db.query(BloqueHorario).filter(BloqueHorario.doctor_id == doctor_id).delete(
        synchronize_session=False
    )
    # Borrar por query evita que SQLAlchemy ponga doctor_id = NULL en las citas
    db.query(Doctor).filter(Doctor.id == doctor_id).delete(synchronize_session=False)
    db.commit()
