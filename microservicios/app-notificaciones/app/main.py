from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Microservicio de Notificaciones",
    description="Servicio encargado de correos, validaciones, compras, pagos y SMS/WhatsApp",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "app-notificaciones"
    }


@app.get("/")
def root():
    return {
        "message": "Microservicio de notificaciones funcionando correctamente"
    }
