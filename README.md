# Proyecto-H — Gestor de Citas Hospitalarias

MVP de gestión de citas médicas con **Python / FastAPI**, SQLAlchemy 2, Pydantic v2, Jinja2.

**Página del proyecto:** https://proyecto-h.iagentek.com.mx

**Código (GitHub):** https://github.com/emilianogenisrod-ux/Proyecto-H

Este repositorio es el código, para que se pueda revisar en clase.
La página de arriba es el sistema ya publicado.
Las claves de la base de datos, MinIO y el inicio de sesión **no van aquí**.
Viven en el servidor, en secretos de Docker. Detalle: [SECURITY.md](SECURITY.md).

## Stack

| Capa | Tecnología |
|------|------------|
| Backend | Python · FastAPI · Uvicorn |
| ORM | SQLAlchemy 2 |
| BD (local) | SQLite (`data/hospital.db`) |
| BD (producción) | PostgreSQL en red interna del servidor (Supabase). Sin acceso público desde GitHub. |
| Objetos | MinIO en red interna del servidor. Sin claves ni consola en este repositorio. |
| Tablas | Prefijo `hospital-` (`hospital-doctors`, `hospital-patients`, …) |

## Metodología

1. **Spec-Driven Development (Spec Kit)** — constitución, spec, plan y tasks en `specs/001-gestor-citas/` y `.specify/`
2. **BMAD Method** — PRD, arquitectura y épicas en `_bmad-output/` (skills en `_bmad/` y `.agents/skills/`)

## Funcionalidades

- **Doctores / Pacientes / Horarios / Citas / Pagos** con API REST y paneles por rol
- **Roles**: admin, director, doctor, paciente
- **Medios**: imágenes, videos y plantillas (disco local o MinIO)
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
cp .env.example .env
```

En `.env` puede poner contraseñas **solo para practicar en su computadora**.
Ese archivo no se sube a GitHub.

## Ejecución

```bash
uvicorn app.main:app --reload
```

Abrir: [http://127.0.0.1:8000](http://127.0.0.1:8000)

Las cuentas del servidor no se publican. Se configuran fuera de este repositorio.

## Qué queda privado

- Contraseñas de entrada
- Contraseña de PostgreSQL / Supabase
- Usuario y clave de MinIO
- Direcciones internas de la base y del almacén de archivos
- El archivo `.env` del servidor

La aplicación, en producción, habla con la base y con MinIO **por la red interna del servidor**.
No hace falta publicar esas puertas en GitHub.

## Base de datos (`hospital-*`)

Esquema SQL: `sql/001_hospital_schema.sql`

- `hospital-doctors`
- `hospital-patients`
- `hospital-schedule_blocks`
- `hospital-appointments`
- `hospital-payments`
- `hospital-media_assets`

## MinIO

Si `MINIO_ENABLED=true` y las claves están en el servidor, los archivos van al bucket `hospital`.
Sin MinIO, se usa la carpeta local `media/`.

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
