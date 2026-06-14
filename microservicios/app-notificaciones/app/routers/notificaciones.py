from fastapi import APIRouter

from app.schemas.notifications import (
    EmailCompraRequest,
    EmailPagoRequest,
    EmailValidacionRequest,
    WhatsAppArchivoRequest,
)
from app.services.email_service import (
    enviar_correo_compra,
    enviar_correo_pago,
    enviar_correo_validacion,
)
from app.services.message_service import enviar_whatsapp_archivo


router = APIRouter(prefix="/notificaciones", tags=["notificaciones"])


@router.post("/email/validacion")
def notificar_validacion(datos: EmailValidacionRequest) -> dict:
    return enviar_correo_validacion(datos)


@router.post("/email/compra")
def notificar_compra(datos: EmailCompraRequest) -> dict:
    return enviar_correo_compra(datos)


@router.post("/email/pago")
def notificar_pago(datos: EmailPagoRequest) -> dict:
    return enviar_correo_pago(datos)


@router.post("/whatsapp/archivo")
def notificar_archivo(datos: WhatsAppArchivoRequest) -> dict:
    return enviar_whatsapp_archivo(datos)