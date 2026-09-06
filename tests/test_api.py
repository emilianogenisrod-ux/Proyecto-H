from datetime import date, datetime, time, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture()
def client():
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def _next_weekday(target_weekday: int) -> date:
    today = date.today()
    days_ahead = (target_weekday - today.weekday() + 7) % 7
    if days_ahead == 0:
        days_ahead = 7
    return today + timedelta(days=days_ahead)


def test_create_doctor(client):
    response = client.post(
        "/api/doctors",
        json={
            "full_name": "Dr. Test",
            "specialty": "Medicina General",
            "consultation_minutes": 30,
            "default_fee": 500,
            "is_active": True,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["full_name"] == "Dr. Test"
    assert data["specialty"] == "Medicina General"


def test_available_slots_and_appointment(client):
    doctor = client.post(
        "/api/doctors",
        json={
            "full_name": "Dr. Slots",
            "specialty": "Cardiología",
            "consultation_minutes": 30,
            "default_fee": 700,
        },
    ).json()

    monday = _next_weekday(0)
    client.post(
        "/api/schedules",
        json={
            "doctor_id": doctor["id"],
            "weekday": 0,
            "start_time": "09:00:00",
            "end_time": "12:00:00",
        },
    )

    slots_resp = client.get(f"/api/doctors/{doctor['id']}/slots", params={"day": monday.isoformat()})
    assert slots_resp.status_code == 200
    slots = slots_resp.json()
    assert len(slots) >= 1

    patient = client.post(
        "/api/patients",
        json={"full_name": "Paciente Test", "document_id": "TEST-001"},
    ).json()

    appt_resp = client.post(
        "/api/appointments",
        json={
            "doctor_id": doctor["id"],
            "patient_id": patient["id"],
            "starts_at": slots[0]["starts_at"],
        },
    )
    assert appt_resp.status_code == 201
    appt = appt_resp.json()
    assert appt["status"] == "scheduled"
    assert appt["payment"]["status"] == "pending"
    assert appt["payment"]["amount"] == 700


def test_appointment_conflict_returns_409(client):
    doctor = client.post(
        "/api/doctors",
        json={
            "full_name": "Dr. Conflicto",
            "specialty": "Pediatría",
            "consultation_minutes": 30,
            "default_fee": 600,
        },
    ).json()

    monday = _next_weekday(0)
    client.post(
        "/api/schedules",
        json={
            "doctor_id": doctor["id"],
            "weekday": 0,
            "start_time": "09:00:00",
            "end_time": "12:00:00",
        },
    )

    slots = client.get(f"/api/doctors/{doctor['id']}/slots", params={"day": monday.isoformat()}).json()
    starts_at = slots[0]["starts_at"]

    patient1 = client.post(
        "/api/patients",
        json={"full_name": "Paciente A", "document_id": "CONF-A"},
    ).json()
    patient2 = client.post(
        "/api/patients",
        json={"full_name": "Paciente B", "document_id": "CONF-B"},
    ).json()

    first = client.post(
        "/api/appointments",
        json={"doctor_id": doctor["id"], "patient_id": patient1["id"], "starts_at": starts_at},
    )
    assert first.status_code == 201

    conflict = client.post(
        "/api/appointments",
        json={"doctor_id": doctor["id"], "patient_id": patient2["id"], "starts_at": starts_at},
    )
    assert conflict.status_code == 409


def test_cancel_frees_slot(client):
    doctor = client.post(
        "/api/doctors",
        json={
            "full_name": "Dr. Cancel",
            "specialty": "Medicina General",
            "consultation_minutes": 30,
            "default_fee": 450,
        },
    ).json()

    monday = _next_weekday(0)
    client.post(
        "/api/schedules",
        json={
            "doctor_id": doctor["id"],
            "weekday": 0,
            "start_time": "09:00:00",
            "end_time": "12:00:00",
        },
    )

    slots_before = client.get(
        f"/api/doctors/{doctor['id']}/slots", params={"day": monday.isoformat()}
    ).json()
    target_slot = slots_before[0]["starts_at"]

    patient = client.post(
        "/api/patients",
        json={"full_name": "Paciente Cancel", "document_id": "CANCEL-001"},
    ).json()

    appt = client.post(
        "/api/appointments",
        json={"doctor_id": doctor["id"], "patient_id": patient["id"], "starts_at": target_slot},
    ).json()

    slots_occupied = client.get(
        f"/api/doctors/{doctor['id']}/slots", params={"day": monday.isoformat()}
    ).json()
    occupied_starts = [s["starts_at"] for s in slots_occupied]
    assert target_slot not in occupied_starts

    cancel_resp = client.post(
        f"/api/appointments/{appt['id']}/cancel",
        json={"reason": "Paciente no puede asistir"},
    )
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "cancelled"

    slots_after = client.get(
        f"/api/doctors/{doctor['id']}/slots", params={"day": monday.isoformat()}
    ).json()
    freed_starts = [s["starts_at"] for s in slots_after]
    assert target_slot in freed_starts
