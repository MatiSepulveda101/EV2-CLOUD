# EV2 Cloud Ecommerce

Proyecto base para un ecommerce con backend FastAPI, microservicio de pagos,
PostgreSQL y Docker Compose.

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
