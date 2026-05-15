from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import configuracion


class Base(DeclarativeBase):
    pass


def _opciones_motor(database_url: str) -> dict:
    if database_url.startswith("sqlite"):
        options: dict = {"connect_args": {"check_same_thread": False}}
        if database_url.endswith(":memory:"):
            options["poolclass"] = StaticPool
        return options
    return {"pool_pre_ping": True}


motor = create_engine(configuracion.database_url, **_opciones_motor(configuracion.database_url))
SesionLocal = sessionmaker(bind=motor, autoflush=False, autocommit=False, expire_on_commit=False)


def obtener_db():
    db = SesionLocal()
    try:
        yield db
    finally:
        db.close()
