import enum
from datetime import datetime, time

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class EstadoCita(str, enum.Enum):
    programada = "scheduled"
    completada = "completed"
    cancelada = "cancelled"
    no_asistio = "no_show"


class EstadoPago(str, enum.Enum):
    pendiente = "pending"
    pagado = "paid"
    parcial = "partial"
    exento = "exempt"
    devolucion = "refund_pending"


# Alias para no romper imports viejos en otras partes
AppointmentStatus = EstadoCita
PaymentStatus = EstadoPago


class Doctor(Base):
    __tablename__ = "hospital-doctors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombre_completo: Mapped[str] = mapped_column("full_name", String(200), nullable=False)
    especialidad: Mapped[str] = mapped_column("specialty", String(120), nullable=False)
    minutos_consulta: Mapped[int] = mapped_column("consultation_minutes", Integer, default=30, nullable=False)
    tarifa: Mapped[float] = mapped_column("default_fee", Float, default=500.0, nullable=False)
    telefono: Mapped[str | None] = mapped_column("phone", String(30), nullable=True)
    correo: Mapped[str | None] = mapped_column("email", String(120), nullable=True, index=True)
    activo: Mapped[bool] = mapped_column("is_active", Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    horarios: Mapped[list["BloqueHorario"]] = relationship(
        back_populates="doctor", cascade="all, delete-orphan"
    )
    citas: Mapped[list["Cita"]] = relationship(back_populates="doctor")


class Paciente(Base):
    __tablename__ = "hospital-patients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombre_completo: Mapped[str] = mapped_column("full_name", String(200), nullable=False)
    documento: Mapped[str] = mapped_column("document_id", String(50), unique=True, nullable=False, index=True)
    telefono: Mapped[str | None] = mapped_column("phone", String(30), nullable=True)
    correo: Mapped[str | None] = mapped_column("email", String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    citas: Mapped[list["Cita"]] = relationship(back_populates="paciente")


# Alias
Patient = Paciente


class BloqueHorario(Base):
    __tablename__ = "hospital-schedule_blocks"
    __table_args__ = (
        UniqueConstraint("doctor_id", "weekday", "start_time", "end_time", name="uq_hospital_schedule"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("hospital-doctors.id"), nullable=False)
    dia_semana: Mapped[int] = mapped_column("weekday", Integer, nullable=False)
    hora_inicio: Mapped[time] = mapped_column("start_time", Time, nullable=False)
    hora_fin: Mapped[time] = mapped_column("end_time", Time, nullable=False)

    doctor: Mapped["Doctor"] = relationship(back_populates="horarios")


ScheduleBlock = BloqueHorario


class Cita(Base):
    __tablename__ = "hospital-appointments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("hospital-doctors.id"), nullable=False)
    paciente_id: Mapped[int] = mapped_column("patient_id", ForeignKey("hospital-patients.id"), nullable=False)
    inicio: Mapped[datetime] = mapped_column("starts_at", DateTime, nullable=False, index=True)
    fin: Mapped[datetime] = mapped_column("ends_at", DateTime, nullable=False)
    estado: Mapped[EstadoCita] = mapped_column(
        "status",
        Enum(
            EstadoCita,
            name="hospital_appointment_status",
            values_callable=lambda x: [e.value for e in x],
        ),
        default=EstadoCita.programada,
        nullable=False,
    )
    notas: Mapped[str | None] = mapped_column("notes", String(500), nullable=True)
    motivo_cancelacion: Mapped[str | None] = mapped_column("cancellation_reason", String(500), nullable=True)
    cancelada_en: Mapped[datetime | None] = mapped_column("cancelled_at", DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    doctor: Mapped["Doctor"] = relationship(back_populates="citas")
    paciente: Mapped["Paciente"] = relationship(back_populates="citas")
    pago: Mapped["Pago | None"] = relationship(
        back_populates="cita", uselist=False, cascade="all, delete-orphan"
    )


Appointment = Cita


class Pago(Base):
    __tablename__ = "hospital-payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    cita_id: Mapped[int] = mapped_column(
        "appointment_id", ForeignKey("hospital-appointments.id"), unique=True, nullable=False
    )
    monto: Mapped[float] = mapped_column("amount", Float, nullable=False)
    estado: Mapped[EstadoPago] = mapped_column(
        "status",
        Enum(
            EstadoPago,
            name="hospital_payment_status",
            values_callable=lambda x: [e.value for e in x],
        ),
        default=EstadoPago.pendiente,
        nullable=False,
    )
    metodo: Mapped[str | None] = mapped_column("method", String(30), nullable=True)
    fecha_pago: Mapped[datetime | None] = mapped_column("paid_at", DateTime, nullable=True)
    notas: Mapped[str | None] = mapped_column("notes", String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    cita: Mapped["Cita"] = relationship(back_populates="pago")


Payment = Pago


class MediaKind(str, enum.Enum):
    image = "image"
    video = "video"
    template = "template"


class MediaAsset(Base):
    __tablename__ = "hospital-media_assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    kind: Mapped[MediaKind] = mapped_column(
        Enum(
            MediaKind,
            name="hospital_media_kind",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        index=True,
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(120), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    folder: Mapped[str] = mapped_column(String(40), nullable=False, default="images")
    storage_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    storage_url: Mapped[str | None] = mapped_column(String(800), nullable=True)
    bucket: Mapped[str | None] = mapped_column(String(120), nullable=True, default="hospital")
    uploaded_by: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
