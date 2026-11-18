from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

Path("data").mkdir(exist_ok=True)

connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from app import models  # noqa: F401
    from sqlalchemy import text

    Base.metadata.create_all(bind=engine)

    # Migración ligera: columnas nuevas / legacy
    with engine.begin() as conn:
        dialect = engine.dialect.name
        if dialect == "sqlite":
            docs = {row[1] for row in conn.execute(text('PRAGMA table_info("hospital-doctors")')).fetchall()}
            pats = {row[1] for row in conn.execute(text('PRAGMA table_info("hospital-patients")')).fetchall()}
            if docs:
                if "email" not in docs:
                    conn.execute(text('ALTER TABLE "hospital-doctors" ADD COLUMN email VARCHAR(120)'))
                if "phone" not in docs:
                    conn.execute(text('ALTER TABLE "hospital-doctors" ADD COLUMN phone VARCHAR(30)'))
                if "sex" not in docs:
                    conn.execute(text('ALTER TABLE "hospital-doctors" ADD COLUMN sex VARCHAR(1)'))
            if pats and "sex" not in pats:
                conn.execute(text('ALTER TABLE "hospital-patients" ADD COLUMN sex VARCHAR(1)'))
        else:
            # PostgreSQL / otros
            conn.execute(text('ALTER TABLE "hospital-doctors" ADD COLUMN IF NOT EXISTS sex VARCHAR(1)'))
            conn.execute(text('ALTER TABLE "hospital-patients" ADD COLUMN IF NOT EXISTS sex VARCHAR(1)'))

    # Nuevo estado de cita: doctor no llegó (enum Postgres)
    if engine.dialect.name == "postgresql":
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            conn.execute(
                text(
                    "ALTER TYPE hospital_appointment_status "
                    "ADD VALUE IF NOT EXISTS 'doctor_absent'"
                )
            )
