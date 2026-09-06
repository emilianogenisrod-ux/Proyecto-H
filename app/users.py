"""Catálogo de usuarios y permisos por rol."""

from __future__ import annotations

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

# Rutas de inicio por rol
ROLE_HOME = {
    ROLE_ADMIN: "/app/admin",
    ROLE_DIRECTOR: "/app/director",
    ROLE_DOCTOR: "/app/doctor",
    ROLE_PATIENT: "/app/patient",
}

# Módulos visibles por rol (para nav / UI)
ROLE_MODULES = {
    ROLE_ADMIN: ["dashboard", "doctors", "patients", "schedules", "appointments", "payments", "users"],
    ROLE_DIRECTOR: ["dashboard", "doctors", "patients", "schedules", "appointments", "payments", "reports"],
    ROLE_DOCTOR: ["dashboard", "schedule", "appointments", "patients"],
    ROLE_PATIENT: ["dashboard", "book", "appointments", "payments", "profile"],
}

USERS: dict[str, dict] = {
    "emiliano@farma": {
        "email": "emiliano@farma",
        "password": "emiliano123",
        "name": "Emiliano Farma",
        "role": ROLE_ADMIN,
        "role_label": ROLE_LABELS[ROLE_ADMIN],
    },
    "sara@farma": {
        "email": "sara@farma",
        "password": "sara123",
        "name": "Sara Farma",
        "role": ROLE_ADMIN,
        "role_label": ROLE_LABELS[ROLE_ADMIN],
    },
    "director@farma": {
        "email": "director@farma",
        "password": "director123",
        "name": "Laura Mendoza",
        "role": ROLE_DIRECTOR,
        "role_label": ROLE_LABELS[ROLE_DIRECTOR],
    },
    "doctor@farma": {
        "email": "doctor@farma",
        "password": "doctor123",
        "name": "Dr. Andrés Vega",
        "role": ROLE_DOCTOR,
        "role_label": ROLE_LABELS[ROLE_DOCTOR],
        "specialty": "Medicina General",
    },
    "paciente@farma": {
        "email": "paciente@farma",
        "password": "paciente123",
        "name": "Sofía Ramírez",
        "role": ROLE_PATIENT,
        "role_label": ROLE_LABELS[ROLE_PATIENT],
        "document_id": "PAC-FARMA-001",
        "phone": "555-0900",
    },
}


def list_demo_accounts() -> list[dict]:
    return [
        {
            "email": u["email"],
            "password": u["password"],
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
