from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Appointment, Payment, PaymentStatus
from app.schemas import PaymentRead, PaymentUpdate

router = APIRouter(prefix="/payments", tags=["Pagos"])


def _serialize_payment(payment: Payment) -> PaymentRead:
    return PaymentRead.model_validate(payment)


@router.get("", response_model=list[PaymentRead])
def list_payments(
    status_filter: PaymentStatus | None = Query(default=None, alias="status"),
    doctor_id: int | None = None,
    db: Session = Depends(get_db),
):
    query = (
        db.query(Payment)
        .join(Appointment)
        .options(joinedload(Payment.appointment))
        .order_by(Payment.created_at.desc())
    )
    if status_filter:
        query = query.filter(Payment.status == status_filter)
    if doctor_id:
        query = query.filter(Appointment.doctor_id == doctor_id)
    return [_serialize_payment(p) for p in query.all()]


@router.get("/{payment_id}", response_model=PaymentRead)
def get_payment(payment_id: int, db: Session = Depends(get_db)):
    payment = db.get(Payment, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    return _serialize_payment(payment)


@router.patch("/{payment_id}", response_model=PaymentRead)
def update_payment(payment_id: int, payload: PaymentUpdate, db: Session = Depends(get_db)):
    payment = db.get(Payment, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Pago no encontrado")

    data = payload.model_dump(exclude_unset=True)
    new_status = data.pop("status", None)
    for field, value in data.items():
        setattr(payment, field, value)

    if new_status:
        payment.status = new_status
        if new_status == PaymentStatus.paid and not payment.paid_at:
            payment.paid_at = datetime.utcnow()
        if new_status in {PaymentStatus.pending, PaymentStatus.partial, PaymentStatus.exempt}:
            if new_status != PaymentStatus.partial:
                payment.paid_at = None

    db.commit()
    db.refresh(payment)
    return _serialize_payment(payment)
