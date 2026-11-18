from datetime import datetime, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.especialidades import ESPECIALIDADES
from app.models import EstadoCita, EstadoPago

EspecialidadNombre = Literal[
    "Medicina General",
    "Pediatría",
    "Ginecología",
    "Dermatología",
]


SexoCodigo = Literal["M", "F"]


class DoctorBase(BaseModel):
    nombre_completo: str = Field(..., min_length=1, max_length=200)
    especialidad: str = Field(..., min_length=1, max_length=120)
    minutos_consulta: int = Field(default=30, ge=5, le=240)
    tarifa: float = Field(default=500.0, ge=0)
    telefono: str | None = Field(default=None, max_length=30)
    correo: str | None = Field(default=None, max_length=120)
    sexo: SexoCodigo | None = None
    activo: bool = True


class DoctorCreate(DoctorBase):
    especialidad: EspecialidadNombre = Field(
        ...,
        description=f"Solo: {', '.join(ESPECIALIDADES)}",
    )


class DoctorUpdate(BaseModel):
    nombre_completo: str | None = Field(default=None, min_length=1, max_length=200)
    especialidad: EspecialidadNombre | None = None
    minutos_consulta: int | None = Field(default=None, ge=5, le=240)
    tarifa: float | None = Field(default=None, ge=0)
    telefono: str | None = Field(default=None, max_length=30)
    correo: str | None = Field(default=None, max_length=120)
    sexo: SexoCodigo | None = None
    activo: bool | None = None


class DoctorRead(DoctorBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class PacienteBase(BaseModel):
    nombre_completo: str = Field(..., min_length=1, max_length=200)
    documento: str = Field(..., min_length=1, max_length=50)
    telefono: str | None = Field(default=None, max_length=30)
    correo: str | None = Field(default=None, max_length=120)
    sexo: SexoCodigo | None = None


class PacienteCreate(PacienteBase):
    pass


class PacienteUpdate(BaseModel):
    nombre_completo: str | None = Field(default=None, min_length=1, max_length=200)
    documento: str | None = Field(default=None, min_length=1, max_length=50)
    telefono: str | None = Field(default=None, max_length=30)
    correo: str | None = Field(default=None, max_length=120)
    sexo: SexoCodigo | None = None


class PacienteRead(PacienteBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


# Alias por si algún import viejo queda
PatientCreate = PacienteCreate
PatientUpdate = PacienteUpdate
PatientRead = PacienteRead


class BloqueHorarioBase(BaseModel):
    dia_semana: int = Field(..., ge=0, le=6)
    hora_inicio: time
    hora_fin: time


class BloqueHorarioCreate(BloqueHorarioBase):
    doctor_id: int


class BloqueHorarioRead(BloqueHorarioBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    doctor_id: int


ScheduleBlockCreate = BloqueHorarioCreate
ScheduleBlockRead = BloqueHorarioRead


class EspacioLibre(BaseModel):
    inicio: datetime
    fin: datetime


SlotRead = EspacioLibre


class CitaCreate(BaseModel):
    doctor_id: int
    paciente_id: int
    inicio: datetime
    notas: str | None = None


class CitaReprogramar(BaseModel):
    inicio: datetime
    doctor_id: int | None = None  # opcional: cambiar de doctor al reagendar


class CitaResultado(BaseModel):
    # Simulación / registro de cómo quedó la cita
    resultado: Literal["completed", "patient_late", "doctor_absent"]
    notas: str | None = Field(default=None, max_length=500)


class CitaCancelar(BaseModel):
    motivo: str = Field(..., min_length=1, max_length=500)


AppointmentCreate = CitaCreate
AppointmentReschedule = CitaReprogramar
AppointmentCancel = CitaCancelar


class PagoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cita_id: int
    monto: float
    estado: EstadoPago
    metodo: str | None
    fecha_pago: datetime | None
    notas: str | None
    created_at: datetime


class PagoUpdate(BaseModel):
    estado: EstadoPago | None = None
    metodo: str | None = Field(default=None, max_length=30)
    monto: float | None = Field(default=None, ge=0)
    notas: str | None = Field(default=None, max_length=500)


PaymentRead = PagoRead
PaymentUpdate = PagoUpdate
PaymentStatus = EstadoPago


class CitaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    doctor_id: int
    paciente_id: int
    inicio: datetime
    fin: datetime
    estado: EstadoCita
    notas: str | None
    motivo_cancelacion: str | None
    cancelada_en: datetime | None
    created_at: datetime
    pago: PagoRead | None = None
    nombre_doctor: str | None = None
    especialidad_doctor: str | None = None
    nombre_paciente: str | None = None
    documento_paciente: str | None = None


AppointmentRead = CitaRead
AppointmentStatus = EstadoCita


class DashboardStats(BaseModel):
    doctors_active: int
    patients_total: int
    appointments_today: int
    payments_pending: int
