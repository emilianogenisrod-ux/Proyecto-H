from datetime import datetime, time

from pydantic import BaseModel, ConfigDict, Field

from app.models import AppointmentStatus, PaymentStatus


class DoctorBase(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=200)
    specialty: str = Field(..., min_length=1, max_length=120)
    consultation_minutes: int = Field(default=30, ge=5, le=240)
    default_fee: float = Field(default=500.0, ge=0)
    is_active: bool = True


class DoctorCreate(DoctorBase):
    pass


class DoctorUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=200)
    specialty: str | None = Field(default=None, min_length=1, max_length=120)
    consultation_minutes: int | None = Field(default=None, ge=5, le=240)
    default_fee: float | None = Field(default=None, ge=0)
    is_active: bool | None = None


class DoctorRead(DoctorBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class PatientBase(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=200)
    document_id: str = Field(..., min_length=1, max_length=50)
    phone: str | None = Field(default=None, max_length=30)
    email: str | None = Field(default=None, max_length=120)


class PatientCreate(PatientBase):
    pass


class PatientUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=200)
    document_id: str | None = Field(default=None, min_length=1, max_length=50)
    phone: str | None = Field(default=None, max_length=30)
    email: str | None = Field(default=None, max_length=120)


class PatientRead(PatientBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class ScheduleBlockBase(BaseModel):
    weekday: int = Field(..., ge=0, le=6)
    start_time: time
    end_time: time


class ScheduleBlockCreate(ScheduleBlockBase):
    doctor_id: int


class ScheduleBlockRead(ScheduleBlockBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    doctor_id: int


class SlotRead(BaseModel):
    starts_at: datetime
    ends_at: datetime


class AppointmentCreate(BaseModel):
    doctor_id: int
    patient_id: int
    starts_at: datetime
    notes: str | None = None


class AppointmentReschedule(BaseModel):
    starts_at: datetime


class AppointmentCancel(BaseModel):
    reason: str = Field(..., min_length=1, max_length=500)


class PaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    appointment_id: int
    amount: float
    status: PaymentStatus
    method: str | None
    paid_at: datetime | None
    notes: str | None
    created_at: datetime


class PaymentUpdate(BaseModel):
    status: PaymentStatus | None = None
    method: str | None = Field(default=None, max_length=30)
    amount: float | None = Field(default=None, ge=0)
    notes: str | None = Field(default=None, max_length=500)


class AppointmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    doctor_id: int
    patient_id: int
    starts_at: datetime
    ends_at: datetime
    status: AppointmentStatus
    notes: str | None
    cancellation_reason: str | None
    cancelled_at: datetime | None
    created_at: datetime
    payment: PaymentRead | None = None
    doctor_name: str | None = None
    patient_name: str | None = None
    patient_document: str | None = None


class DashboardStats(BaseModel):
    doctors_active: int
    patients_total: int
    appointments_today: int
    payments_pending: int
