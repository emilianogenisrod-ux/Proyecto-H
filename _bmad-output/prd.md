# PRD — Proyecto-H: Gestor de Citas Hospitalarias

**Método**: BMAD BMM · **Idioma**: Español · **Fecha**: 2026-09-05  
**Origen Spec Kit**: `specs/001-gestor-citas/spec.md`

## Visión

Permitir a un hospital pequeño/mediano gestionar agendas médicas, citas, cancelaciones y cobros asociados desde una sola aplicación web local.

## Problema

Recepciones pierden tiempo con agendas en papel/Excel: dobles reservas, horarios confusos y cobros desconectados de la cita.

## Usuarios

| Rol | Necesidad |
|-----|-----------|
| Recepción | Agendar, cancelar, reprogramar, ver slots |
| Caja | Agenda de pagos por estado |
| Admin | Mantener doctores, pacientes y horarios |
| Doctor | (MVP) consultado vía listados de citas |

## Alcance MVP

Incluye: doctores, pacientes, horarios semanales, slots, citas, cancelaciones, reprogramación, pagos simulados, dashboard, seed.  
Excluye: pasarela real, HIS/EHR, notificaciones SMS/email, multi-sede, autenticación fuerte.

## Épicas

1. **E1 Maestros** — Doctores y pacientes
2. **E2 Disponibilidad** — Horarios y slots
3. **E3 Citas** — Reserva, cancelación, reprogramación
4. **E4 Pagos** — Estados y agenda de cobros
5. **E5 Operación** — Dashboard y demo seed

## Criterios de éxito

Ver SC-001…SC-005 en la spec Spec Kit. Demo local funcional en <5 minutos tras `pip install` + `uvicorn`.
