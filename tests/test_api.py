from datetime import date, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

engine = create_engine(
    "sqlite://",
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


def _proximo_dia(weekday: int) -> date:
    hoy = date.today()
    dias = (weekday - hoy.weekday() + 7) % 7
    if dias == 0:
        dias = 7
    return hoy + timedelta(days=dias)


def test_crear_doctor(client):
    resp = client.post(
        "/api/doctors",
        json={
            "nombre_completo": "Dr. Test",
            "especialidad": "Medicina General",
            "minutos_consulta": 30,
            "tarifa": 500,
            "activo": True,
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["nombre_completo"] == "Dr. Test"


def test_cita_basica(client):
    doctor = client.post(
        "/api/doctors",
        json={
            "nombre_completo": "Dr. Slots",
            "especialidad": "Medicina General",
            "minutos_consulta": 30,
            "tarifa": 700,
        },
    ).json()

    lunes = _proximo_dia(0)
    client.post(
        "/api/schedules",
        json={
            "doctor_id": doctor["id"],
            "dia_semana": 0,
            "hora_inicio": "09:00:00",
            "hora_fin": "12:00:00",
        },
    )
    espacios = client.get(
        f"/api/doctors/{doctor['id']}/slots", params={"day": lunes.isoformat()}
    ).json()
    assert len(espacios) > 0

    paciente = client.post(
        "/api/patients",
        json={"nombre_completo": "Paciente Test", "documento": "TEST-001"},
    ).json()

    cita = client.post(
        "/api/appointments",
        json={
            "doctor_id": doctor["id"],
            "paciente_id": paciente["id"],
            "inicio": espacios[0]["inicio"],
        },
    )
    assert cita.status_code == 201
    body = cita.json()
    assert body["estado"] == "scheduled"
    assert body["pago"]["estado"] == "pending"
    assert body["pago"]["monto"] == 700


def test_traslape_devuelve_409(client):
    doctor = client.post(
        "/api/doctors",
        json={
            "nombre_completo": "Dr. Conflicto",
            "especialidad": "Pediatría",
            "minutos_consulta": 30,
            "tarifa": 600,
        },
    ).json()
    lunes = _proximo_dia(0)
    client.post(
        "/api/schedules",
        json={
            "doctor_id": doctor["id"],
            "dia_semana": 0,
            "hora_inicio": "09:00:00",
            "hora_fin": "12:00:00",
        },
    )
    inicio = client.get(
        f"/api/doctors/{doctor['id']}/slots", params={"day": lunes.isoformat()}
    ).json()[0]["inicio"]

    p1 = client.post("/api/patients", json={"nombre_completo": "A", "documento": "CONF-A"}).json()
    p2 = client.post("/api/patients", json={"nombre_completo": "B", "documento": "CONF-B"}).json()

    primero = client.post(
        "/api/appointments",
        json={"doctor_id": doctor["id"], "paciente_id": p1["id"], "inicio": inicio},
    )
    assert primero.status_code == 201

    conflicto = client.post(
        "/api/appointments",
        json={"doctor_id": doctor["id"], "paciente_id": p2["id"], "inicio": inicio},
    )
    assert conflicto.status_code == 409


def test_mismo_horario_concurrente(client):
    doctor = client.post(
        "/api/doctors",
        json={
            "nombre_completo": "Dr. Race",
            "especialidad": "Dermatología",
            "minutos_consulta": 30,
            "tarifa": 500,
        },
    ).json()
    lunes = _proximo_dia(0)
    client.post(
        "/api/schedules",
        json={
            "doctor_id": doctor["id"],
            "dia_semana": 0,
            "hora_inicio": "09:00:00",
            "hora_fin": "12:00:00",
        },
    )
    inicio = client.get(
        f"/api/doctors/{doctor['id']}/slots", params={"day": lunes.isoformat()}
    ).json()[0]["inicio"]
    p1 = client.post("/api/patients", json={"nombre_completo": "Race A", "documento": "RACE-A"}).json()
    p2 = client.post("/api/patients", json={"nombre_completo": "Race B", "documento": "RACE-B"}).json()

    def reservar(paciente_id: int):
        return client.post(
            "/api/appointments",
            json={"doctor_id": doctor["id"], "paciente_id": paciente_id, "inicio": inicio},
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(reservar, p1["id"]), pool.submit(reservar, p2["id"])]
        codes = sorted(f.result().status_code for f in as_completed(futures))

    assert codes.count(201) == 1
    assert 409 in codes
    listado = client.get("/api/appointments", params={"doctor_id": doctor["id"]}).json()
    activas = [c for c in listado if c["inicio"] == inicio and c["estado"] == "scheduled"]
    assert len(activas) == 1


def test_cancelar_libera_horario(client):
    doctor = client.post(
        "/api/doctors",
        json={
            "nombre_completo": "Dr. Cancel",
            "especialidad": "Medicina General",
            "minutos_consulta": 30,
            "tarifa": 450,
        },
    ).json()
    lunes = _proximo_dia(0)
    client.post(
        "/api/schedules",
        json={
            "doctor_id": doctor["id"],
            "dia_semana": 0,
            "hora_inicio": "09:00:00",
            "hora_fin": "12:00:00",
        },
    )
    slot = client.get(
        f"/api/doctors/{doctor['id']}/slots", params={"day": lunes.isoformat()}
    ).json()[0]["inicio"]
    paciente = client.post(
        "/api/patients",
        json={"nombre_completo": "Paciente Cancel", "documento": "CANCEL-001"},
    ).json()

    cita = client.post(
        "/api/appointments",
        json={"doctor_id": doctor["id"], "paciente_id": paciente["id"], "inicio": slot},
    ).json()

    cancel = client.post(
        f"/api/appointments/{cita['id']}/cancel",
        json={"motivo": "No puede asistir"},
    )
    assert cancel.status_code == 200
    assert cancel.json()["estado"] == "cancelled"
    assert cancel.json()["pago"]["estado"] == "exempt"

    libres = client.get(
        f"/api/doctors/{doctor['id']}/slots", params={"day": lunes.isoformat()}
    ).json()
    assert slot in [s["inicio"] for s in libres]


def test_resultado_y_reagendar_con_otro_doctor(client):
    d1 = client.post(
        "/api/doctors",
        json={
            "nombre_completo": "Dra. Uno",
            "especialidad": "Ginecología",
            "sexo": "F",
            "minutos_consulta": 30,
            "tarifa": 500,
        },
    ).json()
    d2 = client.post(
        "/api/doctors",
        json={
            "nombre_completo": "Dra. Dos",
            "especialidad": "Ginecología",
            "sexo": "F",
            "minutos_consulta": 30,
            "tarifa": 500,
        },
    ).json()
    lunes = _proximo_dia(0)
    for doctor_id in (d1["id"], d2["id"]):
        client.post(
            "/api/schedules",
            json={
                "doctor_id": doctor_id,
                "dia_semana": 0,
                "hora_inicio": "09:00:00",
                "hora_fin": "13:00:00",
            },
        )
    paciente = client.post(
        "/api/patients",
        json={"nombre_completo": "Paciente Mujer", "documento": "GIN-T-1", "sexo": "F"},
    ).json()
    slot = client.get(
        f"/api/doctors/{d1['id']}/slots", params={"day": lunes.isoformat()}
    ).json()[0]["inicio"]
    cita = client.post(
        "/api/appointments",
        json={"doctor_id": d1["id"], "paciente_id": paciente["id"], "inicio": slot},
    ).json()

    ausente = client.post(
        f"/api/appointments/{cita['id']}/outcome",
        json={"resultado": "doctor_absent"},
    )
    assert ausente.status_code == 200
    assert ausente.json()["estado"] == "doctor_absent"

    slot2 = client.get(
        f"/api/doctors/{d2['id']}/slots", params={"day": lunes.isoformat()}
    ).json()[0]["inicio"]
    reagendada = client.post(
        f"/api/appointments/{cita['id']}/reschedule",
        json={"inicio": slot2, "doctor_id": d2["id"]},
    )
    assert reagendada.status_code == 200
    body = reagendada.json()
    assert body["doctor_id"] == d2["id"]
    assert body["estado"] == "scheduled"


def test_generar_horarios_siempre_asigna(client):
    a = client.post(
        "/api/doctors",
        json={
            "nombre_completo": "Dr. Primero",
            "especialidad": "Medicina General",
            "minutos_consulta": 30,
            "tarifa": 500,
        },
    ).json()
    b = client.post(
        "/api/doctors",
        json={
            "nombre_completo": "Dr. Segundo",
            "especialidad": "Pediatría",
            "minutos_consulta": 30,
            "tarifa": 500,
        },
    ).json()
    gen_a = client.post(f"/api/doctors/{a['id']}/schedules/generate", json={})
    assert gen_a.status_code == 201
    assert len(gen_a.json()) >= 3

    # Aunque A ya ocupe turnos, B siempre recibe horarios (sin error)
    gen_b = client.post(f"/api/doctors/{b['id']}/schedules/generate", json={})
    assert gen_b.status_code == 201
    assert len(gen_b.json()) >= 3


def test_slots_omit_horas_pasadas_solo_hoy(client, monkeypatch):
    from datetime import datetime as dt

    from app.services import availability as avail

    doctor = client.post(
        "/api/doctors",
        json={
            "nombre_completo": "Dr. Tiempo",
            "especialidad": "Medicina General",
            "minutos_consulta": 30,
            "tarifa": 500,
        },
    ).json()
    hoy = date.today()
    manana = hoy + timedelta(days=1)
    for dia in (hoy.weekday(), manana.weekday()):
        client.post(
            "/api/schedules",
            json={
                "doctor_id": doctor["id"],
                "dia_semana": dia,
                "hora_inicio": "09:00:00",
                "hora_fin": "18:00:00",
            },
        )
    # Finge que en México son las 15:20 de hoy
    monkeypatch.setattr(avail, "ahora_mexico", lambda: dt.combine(hoy, dt.strptime("15:20", "%H:%M").time()))

    slots_hoy = client.get(
        f"/api/doctors/{doctor['id']}/slots", params={"day": hoy.isoformat()}
    ).json()
    assert slots_hoy, "Debe haber slots después de las 15:20"
    assert all(s["inicio"] >= f"{hoy.isoformat()}T15:30:00" for s in slots_hoy)

    # Mañana debe incluir la mañana (10:00), aunque ahora sean las 15:20
    slots_manana = client.get(
        f"/api/doctors/{doctor['id']}/slots", params={"day": manana.isoformat()}
    ).json()
    inicios = [s["inicio"] for s in slots_manana]
    assert f"{manana.isoformat()}T10:00:00" in inicios
    assert f"{manana.isoformat()}T09:00:00" in inicios


def test_borrar_doctor_reparte_entre_varios_misma_especialidad(client):
    saliente = client.post(
        "/api/doctors",
        json={
            "nombre_completo": "Dr. Sale",
            "especialidad": "Medicina General",
            "minutos_consulta": 30,
            "tarifa": 500,
        },
    ).json()
    a = client.post(
        "/api/doctors",
        json={
            "nombre_completo": "Dr. Queda A",
            "especialidad": "Medicina General",
            "minutos_consulta": 30,
            "tarifa": 500,
        },
    ).json()
    b = client.post(
        "/api/doctors",
        json={
            "nombre_completo": "Dr. Queda B",
            "especialidad": "Medicina General",
            "minutos_consulta": 30,
            "tarifa": 500,
        },
    ).json()
    # Otra especialidad: no debe aparecer como receptor
    client.post(
        "/api/doctors",
        json={
            "nombre_completo": "Dra. Pediatra",
            "especialidad": "Pediatría",
            "minutos_consulta": 30,
            "tarifa": 500,
        },
    )

    lunes = _proximo_dia(0)
    for doctor_id in (saliente["id"], a["id"], b["id"]):
        client.post(
            "/api/schedules",
            json={
                "doctor_id": doctor_id,
                "dia_semana": 0,
                "hora_inicio": "09:00:00",
                "hora_fin": "13:00:00",
            },
        )

    slots = client.get(
        f"/api/doctors/{saliente['id']}/slots", params={"day": lunes.isoformat()}
    ).json()
    pacientes = []
    citas = []
    for i, slot in enumerate(slots[:2]):
        p = client.post(
            "/api/patients",
            json={"nombre_completo": f"Paciente Reasig {i}", "documento": f"REASIG-{i}"},
        ).json()
        pacientes.append(p)
        citas.append(
            client.post(
                "/api/appointments",
                json={
                    "doctor_id": saliente["id"],
                    "paciente_id": p["id"],
                    "inicio": slot["inicio"],
                },
            ).json()
        )

    sin_nuevo = client.delete(f"/api/doctors/{saliente['id']}")
    assert sin_nuevo.status_code == 409
    detalle = sin_nuevo.json()["detail"]
    ids_ofrecidos = {d["id"] for d in detalle["doctores"]}
    assert ids_ofrecidos == {a["id"], b["id"]}
    assert detalle["especialidad"] == "Medicina General"

    ok = client.delete(
        f"/api/doctors/{saliente['id']}",
        params={
            "redistribuir": "true",
            "doctor_ids": f"{a['id']},{b['id']}",
        },
    )
    assert ok.status_code == 204

    destinos = {
        client.get(f"/api/appointments/{c['id']}").json()["doctor_id"] for c in citas
    }
    assert destinos == {a["id"], b["id"]}
    assert client.get(f"/api/doctors/{saliente['id']}").status_code == 404


def test_borrar_paciente_con_citas(client):
    doctor = client.post(
        "/api/doctors",
        json={
            "nombre_completo": "Dr. Para Borrar Paciente",
            "especialidad": "Medicina General",
            "minutos_consulta": 30,
            "tarifa": 400,
        },
    ).json()
    lunes = _proximo_dia(0)
    client.post(
        "/api/schedules",
        json={
            "doctor_id": doctor["id"],
            "dia_semana": 0,
            "hora_inicio": "09:00:00",
            "hora_fin": "12:00:00",
        },
    )
    paciente = client.post(
        "/api/patients",
        json={"nombre_completo": "Paciente Borrar", "documento": "DEL-PAT-1"},
    ).json()
    slot = client.get(
        f"/api/doctors/{doctor['id']}/slots", params={"day": lunes.isoformat()}
    ).json()[0]["inicio"]
    cita = client.post(
        "/api/appointments",
        json={
            "doctor_id": doctor["id"],
            "paciente_id": paciente["id"],
            "inicio": slot,
        },
    ).json()

    ok = client.delete(f"/api/patients/{paciente['id']}")
    assert ok.status_code == 204
    assert client.get(f"/api/patients/{paciente['id']}").status_code == 404
    assert client.get(f"/api/appointments/{cita['id']}").status_code == 404
