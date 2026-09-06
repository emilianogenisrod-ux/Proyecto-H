# Feature Specification: Gestor de Citas Hospitalarias

**Feature Branch**: `001-gestor-citas`

**Created**: 2026-09-05

**Status**: Active

**Input**: User description: "Hacer gestor de Citas para un hospital. Incluyendo horarios disponibles, agendas de pagos, cancelaciones, etc. Con doctores, pacientes, citas, etc."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Agendar cita con horario disponible (Priority: P1)

Como recepción/paciente, quiero ver horarios libres de un doctor y reservar una cita para una fecha/hora concreta.

**Why this priority**: Es el valor central del producto; sin reservas no hay sistema.

**Independent Test**: Crear doctor con agenda, consultar slots libres, reservar cita y verificar que el slot desaparece.

**Acceptance Scenarios**:

1. **Given** un doctor con horario laboral y sin citas, **When** consulto disponibilidad del día, **Then** veo slots libres generados por duración de consulta.
2. **Given** un slot libre, **When** reservo con paciente válido, **Then** la cita queda `scheduled` y el slot deja de estar disponible.
3. **Given** un slot ya reservado, **When** otro usuario intenta reservarlo, **Then** el sistema rechaza con error de conflicto.

---

### User Story 2 - Gestionar doctores y pacientes (Priority: P1)

Como administrador, quiero registrar y editar doctores (especialidad, agenda) y pacientes (datos de contacto).

**Why this priority**: Sin maestros de personas no se pueden crear citas.

**Independent Test**: CRUD de doctor y paciente vía API/UI y listados visibles.

**Acceptance Scenarios**:

1. **Given** datos válidos de doctor, **When** lo creo, **Then** aparece en el listado con especialidad y activo.
2. **Given** datos válidos de paciente, **When** lo creo, **Then** aparece en el listado y puede usarse en citas.
3. **Given** un doctor inactivo, **When** intento agendar, **Then** el sistema lo rechaza.

---

### User Story 3 - Cancelar y reprogramar citas (Priority: P2)

Como recepción, quiero cancelar una cita con motivo o reprogramarla a otro slot libre.

**Why this priority**: Operación diaria crítica tras el agendamiento.

**Independent Test**: Cancelar libera el slot; reprogramar mueve la cita sin duplicar.

**Acceptance Scenarios**:

1. **Given** una cita `scheduled`, **When** la cancelo con motivo, **Then** pasa a `cancelled`, queda registro del motivo y el horario vuelve a estar libre.
2. **Given** una cita `scheduled`, **When** la reprogramo a un slot libre, **Then** conserva paciente/doctor y actualiza fecha/hora.
3. **Given** una cita ya `cancelled`, **When** intento cancelarla de nuevo, **Then** se rechaza.

---

### User Story 4 - Agenda de pagos (Priority: P2)

Como caja/recepción, quiero registrar el estado de pago de una cita (pendiente, pagado, parcial, exento) y ver una agenda de cobros.

**Why this priority**: El hospital necesita control financiero básico ligado a citas.

**Independent Test**: Crear pago ligado a cita, listar por estado/fecha, marcar como pagado.

**Acceptance Scenarios**:

1. **Given** una cita nueva, **When** se crea, **Then** nace un registro de pago `pending` con monto según especialidad o monto fijo configurable.
2. **Given** un pago pendiente, **When** lo marco como `paid`, **Then** queda registrado método, fecha y monto.
3. **Given** filtros de agenda de pagos, **When** filtro por `pending`, **Then** solo veo cobros pendientes.

---

### User Story 5 - Panel operativo del día (Priority: P3)

Como recepción, quiero un dashboard del día con citas, cancelaciones y pagos pendientes.

**Why this priority**: Mejora operativa; no bloquea el MVP de reservas.

**Independent Test**: Con datos seed, el dashboard muestra conteos coherentes.

**Acceptance Scenarios**:

1. **Given** citas del día, **When** abro el panel, **Then** veo totales por estado y lista del día.

---

### Edge Cases

- ¿Qué ocurre si se intenta agendar en el pasado? → Rechazo.
- ¿Qué ocurre si el doctor no tiene bloque de horario ese día? → Sin slots.
- ¿Cancelación con pago ya `paid`? → Cita cancelada; pago queda `refund_pending` (simulado).
- ¿Solape parcial de horarios? → No permitido; validación por intervalo.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema MUST permitir CRUD de doctores (nombre, especialidad, duración de consulta, activo).
- **FR-002**: El sistema MUST permitir CRUD de pacientes (nombre, documento, teléfono, email).
- **FR-003**: El sistema MUST permitir definir horarios semanales por doctor (día, hora inicio/fin).
- **FR-004**: El sistema MUST calcular slots disponibles a partir de horario − citas no canceladas.
- **FR-005**: El sistema MUST permitir crear citas ligando doctor, paciente, fecha/hora e importe.
- **FR-006**: El sistema MUST impedir doble reserva del mismo doctor en el mismo intervalo.
- **FR-007**: El sistema MUST permitir cancelar citas con motivo y timestamp.
- **FR-008**: El sistema MUST permitir reprogramar citas a slots libres.
- **FR-009**: El sistema MUST mantener agenda de pagos por cita (estados: pending, paid, partial, exempt, refund_pending).
- **FR-010**: El sistema MUST exponer UI web en español para operar doctores, pacientes, citas, horarios y pagos.
- **FR-011**: El sistema MUST incluir datos de demostración (seed) para arranque rápido.
- **FR-012**: El sistema MUST persistir datos en base SQLite local del proyecto.

### Key Entities

- **Doctor**: profesional de salud con especialidad y duración de consulta.
- **Patient**: persona atendida.
- **ScheduleBlock**: bloque semanal de disponibilidad del doctor.
- **Appointment**: cita entre doctor y paciente en un intervalo.
- **Payment**: cobro asociado a una cita.
- **Cancellation**: motivo y metadatos al cancelar (puede vivir en Appointment).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un operador puede registrar doctor, paciente y agendar cita en menos de 3 minutos en demo.
- **SC-002**: 0 dobles reservas en pruebas de conflicto concurrente básico.
- **SC-003**: Cancelar una cita libera el slot en la siguiente consulta de disponibilidad.
- **SC-004**: La agenda de pagos lista correctamente todos los pendientes del día.
- **SC-005**: Arranque local documentado en README con un solo comando de API + UI.
