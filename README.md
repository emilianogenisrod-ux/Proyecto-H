# Proyecto-H — Gestor de Citas Hospitalarias

Aplicación web para citas médicas con Python / FastAPI, SQLAlchemy 2, Pydantic v2 y Jinja2.

## Enlace de la página

**Abrir el sistema:** https://proyecto-h.iagentek.com.mx/login

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
- Especialidades fijas: Medicina General, Pediatría, Ginecología, Dermatología
- Agenda con hora de Ciudad de México (hoy oculta horas pasadas; días futuros muestran todos los turnos)
- Generación de horarios semanales y reasignación de citas al eliminar un doctor
- Datos de ejemplo si la base está vacía

## Privacidad

- `.env` y secretos **no** se suben al repositorio (usar `.env.example`)
- Contraseñas solo en el servidor / `.env` local (`USER_PASSWORDS_JSON`)
- La pantalla de login no muestra correos ni claves

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
specs/               # Spec Kit
_bmad-output/        # BMAD
```
