# Proyecto-H Constitution
<!-- Hospital Appointment Manager — Spec-Driven + BMAD -->

## Core Principles

### I. Domain-First Clarity
El dominio hospitalario (doctores, pacientes, citas, horarios, pagos y cancelaciones)
es la fuente de verdad. Toda feature debe mapearse a entidades y reglas de negocio
explícitas antes de escribir código. No se implementan pantallas o endpoints sin
historia de usuario aceptada en la spec.

### II. Spec Before Code (NON-NEGOTIABLE)
El flujo Spec Kit es obligatorio: constitution → specify → plan → tasks → implement →
converge. BMAD refuerza el mismo ciclo con PRD, arquitectura y stories. El código
sirve a la especificación; si divergen, se actualiza la spec o se corrige el código.

### III. Safety & Privacy by Default
Datos de pacientes y pagos se tratan como sensibles. Validación de entrada,
auditoría de cancelaciones y estados de pago claros son obligatorios. No se exponen
secretos en el repositorio. Autenticación básica por roles (admin, recepción,
doctor, paciente) en el MVP.

### IV. Availability & Consistency of Schedules
Los horarios disponibles deben derivarse de agendas de doctores menos citas
confirmadas. No se permiten dobles reservas del mismo slot. Cancelaciones liberan
el horario de inmediato. Pagos pendientes no bloquean la vista de agenda, pero sí
marcan el estado de la cita.

### V. Simplicity & Traceability
Preferir una arquitectura monolítica clara (API + frontend) sobre microservicios.
Cada decisión técnica debe trazarse a un requisito (FR/NFR). YAGNI: no añadir
pasarelas de pago reales ni EHR externos en el MVP salvo que la spec lo pida.

## Stack Constraints

- Backend: Python 3.11+ con FastAPI, SQLAlchemy y SQLite (dev) / PostgreSQL-ready.
- Frontend: interfaz web moderna servida desde el mismo proyecto (HTML/CSS/JS o
  plantillas ligeras), usable en escritorio y móvil.
- Idioma de producto y documentación: español.
- Repositorio: `proyecto-H` → `https://github.com/emilianogenisrod-ux/Proyecto-H.git`.

## Development Workflow

1. Spec Kit define qué construir (spec/plan/tasks).
2. BMAD profundiza PRD, arquitectura y epics/stories cuando el alcance lo requiera.
3. Implementación por tareas priorizadas (P1 primero).
4. Convergencia: verificar spec ↔ código antes de dar por cerrado un epic.
5. Commits convencionales; push solo a `main` cuando el MVP sea demostrable.

## Governance

Esta constitución prevalece sobre prácticas ad hoc. Toda enmienda requiere:
documento actualizado, justificación y fecha. Los agentes (Spec Kit / BMAD) deben
leerla antes de planificar o implementar.

**Version**: 1.0.0 | **Ratified**: 2026-09-05 | **Last Amended**: 2026-09-05
