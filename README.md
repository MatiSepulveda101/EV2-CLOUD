# EV2 Cloud Ecommerce

Ecommerce full stack listo para levantar con Docker Compose.

Incluye frontend Angular, backend FastAPI, PostgreSQL y un microservicio de pagos
integrado con MercadoPago.

## Estructura

```text
EV2-CLOUD/
  backend/                 API principal FastAPI
  frontend/                Tienda Angular
  microservicios/app-pagos Microservicio de pagos
  documentacion/           Documentacion tecnica
  infraestructura/         Notas de infraestructura y despliegue futuro
  docker-compose.yml       Orquestacion local
```

## Levantar todo

Desde la raiz del proyecto:

```powershell
docker compose up --build
```

URLs:

```text
Frontend:       http://localhost:4200
Backend API:    http://localhost:8000/docs
Backend health: http://localhost:8000/health
Pagos API:      http://localhost:8002/docs
Pagos health:   http://localhost:8002/health
```

El catalogo se puede ver sin iniciar sesion. El login se solicita cuando el
usuario quiere agregar productos al carrito, abrir el carrito o revisar compras.

## Credenciales de MercadoPago

El proyecto levanta sin credenciales, pero el checkout real necesita
`MP_ACCESS_TOKEN`.

Para usar pagos reales:

```powershell
Copy-Item .env.example .env
notepad .env
docker compose up --build
```

Completa en `.env`:

```text
MP_ACCESS_TOKEN=TU_ACCESS_TOKEN
MP_PUBLIC_KEY=TU_PUBLIC_KEY
```

No subas `.env` a GitHub.

## Flujo de prueba

1. Abrir `http://localhost:4200`.
2. Ver productos sin iniciar sesion.
3. Presionar `Agregar al carro`.
4. Iniciar sesion o crear cuenta.
5. Agregar productos y abrir carrito.
6. Ir a pagar.
7. Revisar estado de la orden.

## Comandos utiles

```powershell
docker compose ps
docker compose logs -f backend
docker compose logs -f app-pagos
docker compose down
docker compose down -v
```

`docker compose down -v` borra la base local de PostgreSQL.

## GitHub

El repositorio ignora archivos pesados o sensibles:

```text
.env
backend/.venv
node_modules
dist
.angular
postgres_data
```

La documentacion tecnica completa esta en `documentacion/`.
