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

    # Migración ligera solo en SQLite (columnas legacy)
    if not settings.DATABASE_URL.startswith("sqlite"):
        return

    with engine.begin() as conn:
        cols = {row[1] for row in conn.execute(text('PRAGMA table_info("hospital-doctors")')).fetchall()}
        if cols:
            if "email" not in cols:
                conn.execute(text('ALTER TABLE "hospital-doctors" ADD COLUMN email VARCHAR(120)'))
            if "phone" not in cols:
                conn.execute(text('ALTER TABLE "hospital-doctors" ADD COLUMN phone VARCHAR(30)'))
