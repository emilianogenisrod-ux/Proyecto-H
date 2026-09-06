# Data Model: Gestor de Citas

## Doctor
| Field | Type | Notes |
|-------|------|-------|
| id | int PK | |
| full_name | str | required |
| specialty | str | required |
| consultation_minutes | int | default 30 |
| default_fee | float | default 500 |
| phone | str? | |
| email | str? | |
| is_active | bool | default true |
| created_at | datetime | |

## Patient
| Field | Type | Notes |
|-------|------|-------|
| id | int PK | |
| full_name | str | |
| document_id | str | unique |
| phone | str? | |
| email | str? | |
| created_at | datetime | |

## ScheduleBlock
| Field | Type | Notes |
|-------|------|-------|
| id | int PK | |
| doctor_id | FK Doctor | |
| weekday | int | 0=Lunes … 6=Domingo |
| start_time | time | |
| end_time | time | |

## Appointment
| Field | Type | Notes |
|-------|------|-------|
| id | int PK | |
| doctor_id | FK | |
| patient_id | FK | |
| starts_at | datetime | |
| ends_at | datetime | |
| status | enum | scheduled/completed/cancelled/no_show |
| notes | str? | |
| cancellation_reason | str? | |
| cancelled_at | datetime? | |
| created_at | datetime | |

Unique constraint lógico: no solape de intervalos activos por doctor.

## Payment
| Field | Type | Notes |
|-------|------|-------|
| id | int PK | |
| appointment_id | FK unique | |
| amount | float | |
| status | enum | pending/paid/partial/exempt/refund_pending |
| method | str? | cash/card/transfer |
| paid_at | datetime? | |
| notes | str? | |
| created_at | datetime | |
