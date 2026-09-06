# Proyecto-H — Gestor de Citas Hospitalarias

MVP de gestión de citas médicas con **Python / FastAPI**, SQLAlchemy 2, Pydantic v2, Jinja2.

**Repositorio:** https://github.com/emilianogenisrod-ux/Proyecto-H

## Stack

| Capa | Tecnología |
|------|------------|
| Backend | Python · FastAPI · Uvicorn |
| ORM | SQLAlchemy 2 |
| BD (local) | SQLite (`data/hospital.db`) |
| BD (producción) | Supabase Postgres · `https://iagenteksupabase.iagentek.com.mx` |
| Objetos | MinIO · consola `iagentekminiofront.iagentek.com.mx` · S3 `iagentekminioback.iagentek.com.mx` |
| Tablas | Prefijo `hospital-` (`hospital-doctors`, `hospital-patients`, …) |

## Metodología

1. **Spec-Driven Development (Spec Kit)** — constitución, spec, plan y tasks en `specs/001-gestor-citas/` y `.specify/`
2. **BMAD Method** — PRD, arquitectura y épicas en `_bmad-output/` (skills en `_bmad/` y `.agents/skills/`)

## Funcionalidades

- **Doctores / Pacientes / Horarios / Citas / Pagos** con API REST y paneles por rol
- **Roles**: admin, director, doctor, paciente
- **Medios**: imágenes, videos y plantillas (disco local o MinIO)
- **Documentación** in-app en `/documentacion`
- **Seed** automático si la BD está vacía

## Requisitos

- Python 3.11+

## Instalación

```bash
cd proyecto-H
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env   # ajustar DATABASE_URL / MinIO en producción
```

## Ejecución

```bash
uvicorn app.main:app --reload
```

Abrir: [http://127.0.0.1:8000](http://127.0.0.1:8000)

| Rol | Correo | Contraseña | Panel |
|-----|--------|------------|-------|
| Administrador | `emilio@farma` | `emilio123` | `/app/admin` |
| Director | `director@farma` | `director123` | `/app/director` |
| Doctor | `doctor@farma` | `doctor123` | `/app/doctor` |
| Paciente | `paciente@farma` | `paciente123` | `/app/patient` |

## Base de datos (`hospital-*`)

Esquema SQL: `sql/001_hospital_schema.sql`

- `hospital-doctors`
- `hospital-patients`
- `hospital-schedule_blocks`
- `hospital-appointments`
- `hospital-payments`
- `hospital-media_assets`

## MinIO

Con `MINIO_ENABLED=true` y credenciales en `.env`, uploads van al bucket `hospital` (imágenes, plantillas, videos). Sin MinIO, se usa la carpeta local `media/`.

## Tests

```bash
pytest -v
```

## Estructura

```
app/                 # FastAPI, modelos, routers, templates
sql/                 # Migraciones Postgres / Supabase
media/               # Fallback local de archivos
specs/               # Spec Kit
_bmad-output/        # BMAD
```
