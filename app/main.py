from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app.docs_content import API_ENDPOINTS, TABLES_DOC, get_create_table_sql
from app.auth import (
    authenticate,
    ensure_role_entities,
    get_session_user,
    home_for_user,
    require_roles,
)
from app.config import settings
from app.database import SessionLocal, init_db
from app.routers import appointments, doctors, media, patients, payments, schedules
from app.seed import seed_if_empty
from app.users import ROLE_ADMIN, ROLE_DIRECTOR, ROLE_DOCTOR, ROLE_PATIENT, list_demo_accounts
from app.routers.media import MEDIA_ROOT, ensure_media_dirs

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    ensure_media_dirs()
    db = SessionLocal()
    try:
        seed_if_empty(db)
        ensure_role_entities(db)
    finally:
        db.close()
    yield


app = FastAPI(title=settings.APP_TITLE, lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=settings.SESSION_SECRET, same_site="lax")

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
ensure_media_dirs()
app.mount("/media", StaticFiles(directory=str(MEDIA_ROOT)), name="media")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

app.include_router(doctors.router, prefix="/api")
app.include_router(patients.router, prefix="/api")
app.include_router(schedules.router, prefix="/api")
app.include_router(appointments.router, prefix="/api")
app.include_router(payments.router, prefix="/api")
app.include_router(media.router, prefix="/api")


def _render_error(request: Request, status_code: int, title: str, message: str, detail: str | None = None):
    user = get_session_user(request)
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "title": f"{title} · Proyecto H",
            "status_code": status_code,
            "error_title": title,
            "message": message,
            "detail": detail,
            "home_url": home_for_user(user),
        },
        status_code=status_code,
    )


def _login_context(**extra):
    ctx = {
        "title": "Iniciar sesión · Proyecto H",
        "accounts": list_demo_accounts(),
        "error": None,
        "email_value": "",
    }
    ctx.update(extra)
    return ctx


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    user = get_session_user(request)
    if user:
        return RedirectResponse(url=home_for_user(user), status_code=303)
    return RedirectResponse(url="/login", status_code=303)


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    user = get_session_user(request)
    if user:
        return RedirectResponse(url=home_for_user(user), status_code=303)
    return templates.TemplateResponse(request, "login.html", _login_context())


@app.post("/login", response_class=HTMLResponse)
async def login_submit(request: Request, email: str = Form(...), password: str = Form(...)):
    db = SessionLocal()
    try:
        user = authenticate(email, password, db)
    finally:
        db.close()

    if not user:
        return templates.TemplateResponse(
            request,
            "login.html",
            _login_context(
                error="Correo o contraseña incorrectos. Verifique sus credenciales.",
                email_value=email,
            ),
            status_code=401,
        )

    request.session["user"] = user
    next_url = home_for_user(user)
    return RedirectResponse(
        url=f"/loading?next={next_url}&message=Preparando panel de {user['role_label']}",
        status_code=303,
    )


@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)


@app.get("/loading", response_class=HTMLResponse)
async def loading_page(
    request: Request,
    next: str = "/app",
    message: str = "Preparando su espacio de trabajo",
):
    safe_next = next if next.startswith("/") and not next.startswith("//") else "/app"
    return templates.TemplateResponse(
        request,
        "loading.html",
        {
            "title": "Cargando · Proyecto H",
            "message": message,
            "next_url": safe_next,
            "delay_ms": 1200,
        },
    )


@app.get("/app", response_class=HTMLResponse)
async def app_home(request: Request):
    user = get_session_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    return RedirectResponse(url=home_for_user(user), status_code=303)


@app.get("/documentacion", response_class=HTMLResponse)
async def documentation_page(request: Request):
    user = get_session_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(
        request,
        "documentation.html",
        {
            "title": "Documentación del sistema · Proyecto H",
            "user": user,
            "home_url": home_for_user(user),
            "tables": TABLES_DOC,
            "ddl": get_create_table_sql(),
            "endpoints": API_ENDPOINTS,
        },
    )


@app.get("/app/admin", response_class=HTMLResponse)
async def app_admin(request: Request):
    result = require_roles(request, ROLE_ADMIN)
    if isinstance(result, RedirectResponse):
        return result
    return templates.TemplateResponse(
        request,
        "roles/admin.html",
        {"title": "Administración · Proyecto H", "user": result},
    )


@app.get("/app/director", response_class=HTMLResponse)
async def app_director(request: Request):
    result = require_roles(request, ROLE_DIRECTOR)
    if isinstance(result, RedirectResponse):
        return result
    return templates.TemplateResponse(
        request,
        "roles/director.html",
        {"title": "Dirección · Proyecto H", "user": result},
    )


@app.get("/app/doctor", response_class=HTMLResponse)
async def app_doctor(request: Request):
    result = require_roles(request, ROLE_DOCTOR)
    if isinstance(result, RedirectResponse):
        return result
    return templates.TemplateResponse(
        request,
        "roles/doctor.html",
        {"title": "Consultorio · Proyecto H", "user": result},
    )


@app.get("/app/patient", response_class=HTMLResponse)
async def app_patient(request: Request):
    result = require_roles(request, ROLE_PATIENT)
    if isinstance(result, RedirectResponse):
        return result
    return templates.TemplateResponse(
        request,
        "roles/patient.html",
        {"title": "Portal del paciente · Proyecto H", "user": result},
    )


@app.get("/api/me")
async def api_me(request: Request):
    user = get_session_user(request)
    if not user:
        return JSONResponse({"detail": "No autenticado"}, status_code=401)
    return user


@app.get("/error", response_class=HTMLResponse)
async def error_demo(
    request: Request,
    code: int = 500,
    title: str = "Algo salió mal",
    message: str = "No pudimos completar la solicitud. Intente de nuevo en unos momentos.",
):
    return _render_error(request, code, title, message)


@app.exception_handler(404)
async def not_found_handler(request: Request, _exc):
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        return _render_error(
            request,
            404,
            "Página no encontrada",
            "La ruta que buscó no existe o fue movida.",
            detail=str(request.url.path),
        )
    return JSONResponse({"detail": "Not Found"}, status_code=404)


@app.exception_handler(500)
async def server_error_handler(request: Request, _exc):
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        return _render_error(
            request,
            500,
            "Error del servidor",
            "Ocurrió un problema interno. El equipo técnico ya puede revisar el incidente.",
        )
    return JSONResponse({"detail": "Internal Server Error"}, status_code=500)
