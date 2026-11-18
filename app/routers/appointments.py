from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Cita, Doctor, EstadoCita, EstadoPago, Paciente, Pago
from app.schemas import (
    CitaCancelar,
    CitaCreate,
    CitaRead,
    CitaReprogramar,
    CitaResultado,
    DashboardStats,
)
from app.especialidades import validar_genero_especialidad
from app.services.availability import bloquear_doctor, fecha_agenda_valida, horario_disponible

router = APIRouter(prefix="/appointments", tags=["Citas"])


def _cita_a_respuesta(cita: Cita) -> CitaRead:
    datos = CitaRead.model_validate(cita)
    if cita.doctor:
        datos.nombre_doctor = cita.doctor.nombre_completo
        datos.especialidad_doctor = cita.doctor.especialidad
    if cita.paciente:
        datos.nombre_paciente = cita.paciente.nombre_completo
        datos.documento_paciente = cita.paciente.documento
    return datos


@router.get("/stats/dashboard", response_model=DashboardStats)
def dashboard_stats(db: Session = Depends(get_db)):
    hoy = datetime.now().date()
    inicio_hoy = datetime.combine(hoy, datetime.min.time())
    fin_hoy = inicio_hoy + timedelta(days=1)
    return DashboardStats(
        doctors_active=db.query(Doctor).filter(Doctor.activo.is_(True)).count(),
        patients_total=db.query(Paciente).count(),
        appointments_today=db.query(Cita)
        .filter(
            Cita.inicio >= inicio_hoy,
            Cita.inicio < fin_hoy,
            Cita.estado != EstadoCita.cancelada,
        )
        .count(),
        payments_pending=db.query(Pago).filter(Pago.estado == EstadoPago.pendiente).count(),
    )


@router.get("", response_model=list[CitaRead])
def listar_citas(
    doctor_id: int | None = None,
    paciente_id: int | None = None,
    estado: EstadoCita | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
):
    consulta = (
        db.query(Cita)
        .options(joinedload(Cita.pago), joinedload(Cita.doctor), joinedload(Cita.paciente))
        .order_by(Cita.inicio.desc())
    )
    if doctor_id:
        consulta = consulta.filter(Cita.doctor_id == doctor_id)
    if paciente_id:
        consulta = consulta.filter(Cita.paciente_id == paciente_id)
    if estado:
        consulta = consulta.filter(Cita.estado == estado)
    return [_cita_a_respuesta(c) for c in consulta.all()]


@router.get("/{cita_id}", response_model=CitaRead)
def obtener_cita(cita_id: int, db: Session = Depends(get_db)):
    cita = (
        db.query(Cita)
        .options(joinedload(Cita.pago), joinedload(Cita.doctor), joinedload(Cita.paciente))
        .filter(Cita.id == cita_id)
        .first()
    )
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    return _cita_a_respuesta(cita)


@router.post("", response_model=CitaRead, status_code=status.HTTP_201_CREATED)
def crear_cita(payload: CitaCreate, db: Session = Depends(get_db)):
    doctor = bloquear_doctor(db, payload.doctor_id)
    if not doctor or not doctor.activo:
        raise HTTPException(status_code=404, detail="Doctor no encontrado o inactivo")

    paciente = db.get(Paciente, payload.paciente_id)
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")

    aviso_genero = validar_genero_especialidad(
        doctor.especialidad,
        sexo_doctor=doctor.sexo,
        sexo_paciente=paciente.sexo,
    )
    if aviso_genero:
        raise HTTPException(status_code=400, detail=aviso_genero)

    aviso = fecha_agenda_valida(payload.inicio)
    if aviso:
        raise HTTPException(status_code=400, detail=aviso)

    fin = payload.inicio + timedelta(minutes=doctor.minutos_consulta)
    if not horario_disponible(db, doctor, payload.inicio, fin):
        raise HTTPException(
            status_code=409,
            detail="El doctor no tiene este horario disponible",
        )

    cita = Cita(
        doctor_id=payload.doctor_id,
        paciente_id=payload.paciente_id,
        inicio=payload.inicio,
        fin=fin,
        estado=EstadoCita.programada,
        notas=payload.notas,
    )
    db.add(cita)
    db.flush()
    cita_id = cita.id

    pago = Pago(
        cita_id=cita_id,
        monto=doctor.tarifa,
        estado=EstadoPago.pendiente,
    )
    db.add(pago)
    db.commit()

    cita = (
        db.query(Cita)
        .options(joinedload(Cita.pago), joinedload(Cita.doctor), joinedload(Cita.paciente))
        .filter(Cita.id == cita_id)
        .first()
    )
    return _cita_a_respuesta(cita)


@router.post("/{cita_id}/cancel", response_model=CitaRead)
def cancelar_cita(cita_id: int, payload: CitaCancelar, db: Session = Depends(get_db)):
    cita = (
        db.query(Cita)
        .options(joinedload(Cita.pago), joinedload(Cita.doctor), joinedload(Cita.paciente))
        .filter(Cita.id == cita_id)
        .first()
    )
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    if cita.estado == EstadoCita.cancelada:
        raise HTTPException(status_code=400, detail="La cita ya está cancelada")

    cita.estado = EstadoCita.cancelada
    cita.motivo_cancelacion = payload.motivo
    cita.cancelada_en = datetime.utcnow()

    if cita.pago:
        if cita.pago.estado == EstadoPago.pagado:
            cita.pago.estado = EstadoPago.devolucion
        elif cita.pago.estado == EstadoPago.pendiente:
            cita.pago.estado = EstadoPago.exento

    db.commit()
    db.refresh(cita)
    return _cita_a_respuesta(cita)


@router.post("/{cita_id}/outcome", response_model=CitaRead)
def registrar_resultado_cita(cita_id: int, payload: CitaResultado, db: Session = Depends(get_db)):
    """Simula / registra si la cita se realizó, el paciente llegó tarde o el doctor faltó."""
    cita = (
        db.query(Cita)
        .options(joinedload(Cita.pago), joinedload(Cita.doctor), joinedload(Cita.paciente))
        .filter(Cita.id == cita_id)
        .first()
    )
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    if cita.estado == EstadoCita.cancelada:
        raise HTTPException(status_code=400, detail="La cita está cancelada")
    if cita.estado == EstadoCita.completada:
        raise HTTPException(status_code=400, detail="La cita ya quedó como realizada")

    if payload.resultado == "completed":
        cita.estado = EstadoCita.completada
        nota = "Cita realizada"
        if cita.pago and cita.pago.estado == EstadoPago.pendiente:
            cita.pago.estado = EstadoPago.pagado
            cita.pago.metodo = cita.pago.metodo or "cash"
            cita.pago.fecha_pago = datetime.utcnow()
    elif payload.resultado == "patient_late":
        cita.estado = EstadoCita.no_asistio
        nota = "Paciente llegó tarde / no asistió — puede reagendar"
    else:
        cita.estado = EstadoCita.doctor_ausente
        nota = "Doctor no llegó — el paciente puede reagendar con otro doctor"

    if payload.notas:
        nota = f"{nota}. {payload.notas}"
    cita.notas = f"{cita.notas}. {nota}" if cita.notas else nota

    db.commit()
    db.refresh(cita)
    return _cita_a_respuesta(cita)


@router.post("/{cita_id}/reschedule", response_model=CitaRead)
def reprogramar_cita(cita_id: int, payload: CitaReprogramar, db: Session = Depends(get_db)):
    cita = (
        db.query(Cita)
        .options(joinedload(Cita.pago), joinedload(Cita.doctor), joinedload(Cita.paciente))
        .filter(Cita.id == cita_id)
        .first()
    )
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    if cita.estado == EstadoCita.cancelada:
        raise HTTPException(status_code=400, detail="No se puede reprogramar una cita cancelada")
    if cita.estado == EstadoCita.completada:
        raise HTTPException(status_code=400, detail="No se puede reprogramar una cita ya realizada")

    doctor_id = payload.doctor_id or cita.doctor_id
    # Si el doctor faltó, hay que reagendar con otro doctor
    if cita.estado == EstadoCita.doctor_ausente:
        if not payload.doctor_id or payload.doctor_id == cita.doctor_id:
            raise HTTPException(
                status_code=400,
                detail="Elige otro doctor para reagendar esta cita",
            )

    doctor = bloquear_doctor(db, doctor_id)
    if not doctor or not doctor.activo:
        raise HTTPException(status_code=404, detail="Doctor no encontrado o inactivo")

    paciente = db.get(Paciente, cita.paciente_id)
    aviso_genero = validar_genero_especialidad(
        doctor.especialidad,
        sexo_doctor=doctor.sexo,
        sexo_paciente=paciente.sexo if paciente else None,
    )
    if aviso_genero:
        raise HTTPException(status_code=400, detail=aviso_genero)

    # Al cambiar de doctor por ausencia, conserva la especialidad original si es posible
    if (
        payload.doctor_id
        and cita.doctor
        and doctor.especialidad != cita.doctor.especialidad
        and cita.estado == EstadoCita.doctor_ausente
    ):
        raise HTTPException(
            status_code=400,
            detail="El nuevo doctor debe ser de la misma especialidad",
        )

    aviso = fecha_agenda_valida(payload.inicio)
    if aviso:
        raise HTTPException(status_code=400, detail=aviso)

    fin = payload.inicio + timedelta(minutes=doctor.minutos_consulta)
    if not horario_disponible(db, doctor, payload.inicio, fin, excluir_cita_id=cita.id):
        raise HTTPException(status_code=409, detail="El doctor no tiene este horario disponible")

    cita.doctor_id = doctor.id
    cita.inicio = payload.inicio
    cita.fin = fin
    if cita.estado in (EstadoCita.no_asistio, EstadoCita.doctor_ausente):
        cita.estado = EstadoCita.programada
        extra = "Reagendada tras incidencia"
        cita.notas = f"{cita.notas}. {extra}" if cita.notas else extra

    db.commit()
    db.refresh(cita)
    return _cita_a_respuesta(cita)
