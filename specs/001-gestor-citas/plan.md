# Implementation Plan: Gestor de Citas Hospitalarias

**Branch**: `001-gestor-citas` | **Date**: 2026-09-05 | **Spec**: [spec.md](./spec.md)

## Summary

Construir un MVP monolítico de gestión de citas hospitalarias con FastAPI + SQLAlchemy + SQLite y una UI web en español. Cubrir doctores, pacientes, horarios, citas, cancelaciones/reprogramaciones y agenda de pagos. Flujo: Spec Kit (spec→plan→tasks→implement) + BMAD (PRD/arquitectura/stories).

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: FastAPI, Uvicorn, SQLAlchemy 2.x, Pydantic v2, Jinja2  
**Storage**: SQLite (`data/hospital.db`)  
**Testing**: pytest + httpx AsyncClient  
**Target Platform**: Windows/macOS/Linux local  
**Project Type**: Web app (API + UI estática/plantillas)  
**Performance Goals**: <200ms típico en operaciones locales CRUD  
**Constraints**: Sin pasarela de pago real; montos simulados  
**Scale/Scope**: Demo hospitalaria (decenas de doctores, cientos de citas)

## Constitution Check

- Domain-first: entidades Doctor/Patient/Appointment/Payment/Schedule ✓
- Spec before code: este plan deriva de spec.md ✓
- Safety: validaciones + sin secretos en repo ✓
- Schedules: slots = agenda − citas activas ✓
- Simplicity: monolito FastAPI ✓

## Project Structure

```text
proyecto-H/
├── README.md
├── requirements.txt
├── .gitignore
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── seed.py
│   ├── routers/
│   │   ├── doctors.py
│   │   ├── patients.py
│   │   ├── schedules.py
│   │   ├── appointments.py
│   │   └── payments.py
│   ├── services/
│   │   └── availability.py
│   ├── static/
│   │   ├── css/styles.css
│   │   └── js/app.js
│   └── templates/
│       └── index.html
├── tests/
│   └── test_api.py
├── specs/001-gestor-citas/
└── _bmad-output/
```

## Architecture Decisions

1. **Monolito FastAPI**: una sola app sirve API REST (`/api/...`) y UI (`/`).
2. **Slots calculados**: no se materializan todos los slots; se generan al consultar.
3. **Estados de cita**: `scheduled | completed | cancelled | no_show`.
4. **Pagos**: 1:1 con cita al crear; actualización de estado independiente.
5. **Seed**: doctores, pacientes, horarios y citas demo al arrancar si DB vacía.

## Complexity Tracking

Sin violaciones: no microservicios, no auth compleja en MVP (rol simulado en UI).
