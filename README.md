# EV2 Cloud Ecommerce

Proyecto base para un ecommerce con backend FastAPI, microservicio de pagos,
PostgreSQL y Docker Compose.

La documentacion tecnica esta separada por tema en `documentacion/`.

## Servicios Implementados

- `backend`: API REST FastAPI en puerto `8000`.
- `postgres-db`: PostgreSQL local compatible con AWS RDS.
- `app-pagos`: microservicio externo de pagos, disponible con el perfil `payments`.
- `microservicios/app-pagos`: servicio stateless de pagos con MercadoPago.

## Endpoints Principales

- `GET /health`
- `POST /auth/register`
- `POST /auth/login`
- `GET /products`
- `GET /products/{id}`
- `GET /cart`
- `POST /cart/items`
- `PATCH /cart/items/{id}`
- `DELETE /cart/items/{id}`
- `POST /checkout`
- `GET /orders/{id}`

## Ejecucion Local Python

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:DATABASE_URL="sqlite+pysqlite:///./dev.db"
$env:JWT_SECRET_KEY="local-secret-key-with-enough-length"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

La API queda disponible en `http://127.0.0.1:8000/docs`.

## Ejecucion Con Docker

```powershell
Copy-Item backend\.env.example backend\.env
docker compose up --build postgres-db backend
```

Para incluir `app-pagos`, configura `MP_ACCESS_TOKEN` y `MP_PUBLIC_KEY` en `backend/.env` y ejecuta:

```powershell
docker compose --profile payments up --build
```

## Migraciones

Esta version basica no usa Alembic. FastAPI crea las tablas al iniciar mediante SQLAlchemy (`AUTO_CREATE_TABLES=true`) y carga productos demo si la tabla esta vacia.
