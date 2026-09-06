# Proyecto-H — Gestor de Citas Hospitalarias

MVP de gestión de citas médicas con FastAPI, SQLAlchemy 2, Pydantic v2, Jinja2 y SQLite.

**Repositorio:** https://github.com/emilianogenisrod-ux/Proyecto-H

## Metodología

1. **Spec-Driven Development (Spec Kit)** — constitución, spec, plan y tasks en `specs/001-gestor-citas/` y `.specify/`
2. **BMAD Method** — PRD, arquitectura y épicas en `_bmad-output/` (skills en `_bmad/` y `.agents/skills/`)

## Funcionalidades

- **Doctores**: CRUD con nombre, especialidad, duración de consulta, tarifa default y estado activo
- **Pacientes**: CRUD con documento único, teléfono y email
- **Horarios semanales**: bloques por doctor (Lunes=0 … Domingo=6)
- **Slots disponibles**: cálculo automático excluyendo citas activas
- **Citas**: crear, listar, cancelar (con motivo) y reprogramar, con detección de solapes
- **Pagos**: relación 1:1 con citas (pending, paid, partial, exempt, refund_pending)
- **UI web** en español con pestañas: Dashboard, Doctores, Pacientes, Horarios, Citas, Pagos
- **Seed automático** al iniciar si la base de datos está vacía

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
```

## Ejecución

```bash
uvicorn app.main:app --reload
```

Abrir en el navegador: [http://127.0.0.1:8000](http://127.0.0.1:8000)

La API REST está disponible bajo `/api`. Documentación interactiva en [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

## Tests

```bash
pytest -v
```

## Estructura

```
app/
  main.py           # Punto de entrada FastAPI
  config.py         # Configuración (DATABASE_URL)
  database.py       # Engine, sesión, init_db
  models.py         # Modelos SQLAlchemy
  schemas.py        # Esquemas Pydantic
  seed.py           # Datos iniciales
  routers/          # Endpoints REST
  services/         # Lógica de disponibilidad
  templates/        # Plantilla Jinja2
  static/           # CSS y JS
tests/
  test_api.py       # Tests con pytest
data/
  hospital.db       # Base SQLite (generada al iniciar)
```

## Base de datos

SQLite en `data/hospital.db`. Se crea automáticamente al arrancar la aplicación.
