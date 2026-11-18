from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Cita, EstadoPago, Pago
from app.schemas import PagoRead, PagoUpdate

router = APIRouter(prefix="/payments", tags=["Pagos"])


@router.get("", response_model=list[PagoRead])
def listar_pagos(
    status_filter: EstadoPago | None = Query(default=None, alias="status"),
    doctor_id: int | None = None,
    db: Session = Depends(get_db),
):
    consulta = (
        db.query(Pago)
        .join(Cita)
        .options(joinedload(Pago.cita))
        .order_by(Pago.created_at.desc())
    )
    if status_filter:
        consulta = consulta.filter(Pago.estado == status_filter)
    if doctor_id:
        consulta = consulta.filter(Cita.doctor_id == doctor_id)
    return consulta.all()


@router.get("/{pago_id}", response_model=PagoRead)
def obtener_pago(pago_id: int, db: Session = Depends(get_db)):
    pago = db.get(Pago, pago_id)
    if not pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    return pago


@router.patch("/{pago_id}", response_model=PagoRead)
def actualizar_pago(pago_id: int, payload: PagoUpdate, db: Session = Depends(get_db)):
    pago = db.get(Pago, pago_id)
    if not pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")

    cambios = payload.model_dump(exclude_unset=True)
    nuevo_estado = cambios.pop("estado", None)

    for campo, valor in cambios.items():
        setattr(pago, campo, valor)

    if nuevo_estado is not None:
        pago.estado = nuevo_estado
        if nuevo_estado == EstadoPago.pagado and not pago.fecha_pago:
            pago.fecha_pago = datetime.utcnow()
        if nuevo_estado in {EstadoPago.pendiente, EstadoPago.exento}:
            pago.fecha_pago = None

    db.commit()
    db.refresh(pago)
    return pago
