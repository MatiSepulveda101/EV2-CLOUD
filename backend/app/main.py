from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import configuracion
from app.database import Base, SesionLocal, motor
from app.routers import auth, cart, checkout, orders, products
from app.seed import cargar_productos_demo

# Importa modelos para que SQLAlchemy registre las tablas antes de crear o migrar.
from app import models  # noqa: F401


@asynccontextmanager
async def ciclo_vida(app: FastAPI):
    if configuracion.auto_create_tables:
        Base.metadata.create_all(bind=motor)
        if configuracion.auto_seed_products:
            db = SesionLocal()
            try:
                cargar_productos_demo(db)
            finally:
                db.close()
    yield


API_PREFIX = "/api"

app = FastAPI(
    title=configuracion.app_name,
    version="0.1.0",
    lifespan=ciclo_vida,
    docs_url=f"{API_PREFIX}/docs",
    redoc_url=f"{API_PREFIX}/redoc",
    openapi_url=f"{API_PREFIX}/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=configuracion.lista_origenes_cors,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(products.router, prefix=API_PREFIX)
app.include_router(cart.router, prefix=API_PREFIX)
app.include_router(checkout.router, prefix=API_PREFIX)
app.include_router(orders.router, prefix=API_PREFIX)


@app.get(f"{API_PREFIX}/health", tags=["health"])
def verificar_salud() -> dict[str, str]:
    return {"status": "ok", "service": "backend"}
