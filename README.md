# Proyecto-H — Gestor de Citas Hospitalarias

Aplicación web para citas médicas con Python / FastAPI, SQLAlchemy 2, Pydantic v2 y Jinja2.

**Sitio:** https://proyecto-h.iagentek.com.mx  
**Código:** https://github.com/emilianogenisrod-ux/Proyecto-H

Las claves de base de datos, MinIO y acceso no se suben a este repositorio. Se configuran en el servidor.

## Stack

| Capa | Tecnología |
|------|------------|
| Backend | Python · FastAPI · Uvicorn |
| ORM | SQLAlchemy 2 |
| BD (local) | SQLite (`data/hospital.db`) |
| BD (producción) | PostgreSQL en red interna |
| Archivos | MinIO en red interna |
| Tablas | Prefijo `hospital-` |

## Funcionalidades

- Doctores, pacientes, horarios, citas y pagos
- Roles: admin, director, doctor, paciente
- Medios (imágenes, videos, plantillas)
- Datos de ejemplo si la base está vacía

## Requisitos

- Python 3.11+

## Instalación

```bash
cd proyecto-H
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

## Ejecución

```bash
uvicorn app.main:app --reload
```

Abrir: http://127.0.0.1:8000

## Tests

```bash
pytest -v
```

## Estructura

```
app/                 # FastAPI, modelos, routers, templates
sql/                 # Esquema de tablas
media/               # Archivos locales
specs/               # Spec Kit
_bmad-output/        # BMAD
```
