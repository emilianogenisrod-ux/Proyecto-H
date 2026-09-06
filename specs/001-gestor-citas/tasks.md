# Tasks: Gestor de Citas Hospitalarias

**Input**: plan.md + data-model.md + spec.md  
**Prerequisites**: constitution.md

## Phase 1 — Setup
- [x] T001 Crear estructura `app/`, `tests/`, `requirements.txt`, `.gitignore`, `README.md`
- [x] T002 Configurar FastAPI, SQLAlchemy, DB SQLite y seed automático

## Phase 2 — Foundational (P1)
- [x] T003 Implementar modelos Doctor, Patient, ScheduleBlock, Appointment, Payment
- [x] T004 Implementar schemas Pydantic y routers CRUD doctores/pacientes
- [x] T005 Implementar ScheduleBlock y servicio de disponibilidad de slots
- [x] T006 Implementar citas: crear, listar, conflicto de solape
- [x] T007 Implementar cancelación y reprogramación
- [x] T008 Implementar pagos y agenda de cobros

## Phase 3 — UI (P1/P2)
- [x] T009 UI dashboard + navegación en español
- [x] T010 Pantallas doctores, pacientes, horarios, citas, pagos

## Phase 4 — Quality
- [x] T011 Tests API de conflicto, cancelación y pagos
- [x] T012 Documentar arranque y subir a GitHub `Proyecto-H`

## Parallel opportunities
- T004∥T005 tras T003
- T009∥T011 tras T008
