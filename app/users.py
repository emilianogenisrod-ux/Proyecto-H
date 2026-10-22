"""Catálogo de usuarios y permisos por rol.

Las contraseñas no viven en este archivo. En desarrollo local se leen de
USER_PASSWORDS_JSON en el archivo .env (que no se sube a GitHub).
En el servidor se usan secretos de Docker, fuera del repositorio.
"""

from __future__ import annotations

import json

ROLE_ADMIN = "admin"
ROLE_DIRECTOR = "director"
ROLE_DOCTOR = "doctor"
ROLE_PATIENT = "patient"

ROLE_LABELS = {
    ROLE_ADMIN: "Administrador",
    ROLE_DIRECTOR: "Director",
    ROLE_DOCTOR: "Doctor",
    ROLE_PATIENT: "Paciente",
}

ROLE_HOME = {
    ROLE_ADMIN: "/app/admin",
    ROLE_DIRECTOR: "/app/director",
    ROLE_DOCTOR: "/app/doctor",
    ROLE_PATIENT: "/app/patient",
}

ROLE_MODULES = {
    ROLE_ADMIN: ["dashboard", "doctors", "patients", "schedules", "appointments", "payments", "users"],
    ROLE_DIRECTOR: ["dashboard", "doctors", "patients", "schedules", "appointments", "payments", "reports"],
    ROLE_DOCTOR: ["dashboard", "schedule", "appointments", "patients"],
    ROLE_PATIENT: ["dashboard", "book", "appointments", "payments", "profile"],
}

USERS: dict[str, dict] = {
    "emiliano@farma": {
        "email": "emiliano@farma",
        "name": "Emiliano Farma",
        "role": ROLE_ADMIN,
        "role_label": ROLE_LABELS[ROLE_ADMIN],
    },
    "sara@farma": {
        "email": "sara@farma",
        "name": "Sara Farma",
        "role": ROLE_ADMIN,
        "role_label": ROLE_LABELS[ROLE_ADMIN],
    },
    "director@farma": {
        "email": "director@farma",
        "name": "Laura Mendoza",
        "role": ROLE_DIRECTOR,
        "role_label": ROLE_LABELS[ROLE_DIRECTOR],
    },
    "doctor@farma": {
        "email": "doctor@farma",
        "name": "Dr. Andrés Vega",
        "role": ROLE_DOCTOR,
        "role_label": ROLE_LABELS[ROLE_DOCTOR],
        "specialty": "Medicina General",
    },
    "paciente@farma": {
        "email": "paciente@farma",
        "name": "Sofía Ramírez",
        "role": ROLE_PATIENT,
        "role_label": ROLE_LABELS[ROLE_PATIENT],
        "document_id": "PAC-FARMA-001",
        "phone": "555-0900",
    },
}


def password_for(email: str) -> str | None:
    from app.config import settings

    raw = (settings.USER_PASSWORDS_JSON or "").strip()
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    value = data.get((email or "").strip().lower())
    return value if isinstance(value, str) and value else None


def list_demo_accounts() -> list[dict]:
    return [
        {
            "email": u["email"],
            "name": u["name"],
            "role": u["role"],
            "role_label": u["role_label"],
        }
        for u in USERS.values()
    ]


def public_user(record: dict, extras: dict | None = None) -> dict:
    data = {
        "email": record["email"],
        "name": record["name"],
        "role": record["role"],
        "role_label": record["role_label"],
        "home": ROLE_HOME[record["role"]],
        "modules": ROLE_MODULES[record["role"]],
    }
    if extras:
        data.update(extras)
    return data
