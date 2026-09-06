# Arquitectura — Proyecto-H

**Fecha**: 2026-09-05 · **BMAD**: bmad-architecture + Spec Kit plan

## Vista lógica

```
Browser UI (templates + static JS)
        │  fetch /api/*
        ▼
FastAPI routers (doctors, patients, schedules, appointments, payments)
        │
        ├── services/availability (slots)
        └── SQLAlchemy models → SQLite
```

## Decisiones

| Decisión | Elección | Por qué |
|----------|----------|---------|
| Estilo app | Monolito | MVP simple, un deploy |
| API | REST JSON | UI y tests fáciles |
| DB | SQLite | cero infra local |
| Slots | Calculados | evita explosión de filas |
| Pagos | Simulados 1:1 | sin PCI |

## Contratos clave

- `GET /api/schedules/availability?doctor_id=&date=` → lista de slots ISO
- `POST /api/appointments` → cita + payment pending; 409 si solapa
- `POST /api/appointments/{id}/cancel` → libera slot; paid→refund_pending
- `GET /api/payments?status=pending` → agenda de cobros

## Riesgos

- Concurrencia SQLite limitada → aceptable en demo
- Sin auth → no exponer a internet público
