# Frontend ElectroFactory

Aplicacion Angular para la tienda del proyecto EV2.

## Docker

Normalmente no se levanta por separado. Desde la raiz:

```powershell
docker compose up --build
```

El frontend queda disponible en:

```text
http://localhost:4200
```

## Desarrollo local

```powershell
cd frontend
npm install
npm start
```

El cliente consume el backend en:

```text
http://127.0.0.1:8000
```

No abras archivos HTML internos directamente desde el navegador. Angular debe
compilar la aplicacion mediante `npm start` o Docker.
