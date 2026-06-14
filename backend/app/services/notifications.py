from __future__ import annotations

import httpx

from app.config import configuracion


def enviar_email_validacion(email: str, nombre: str, codigo: str) -> dict:
    url = f"{configuracion.notifications_service_url.rstrip('/')}/notificaciones/email/validacion"

    payload = {
        "email": email,
        "nombre": nombre,
        "codigo": codigo,
    }

    try:
        respuesta = httpx.post(url, json=payload, timeout=5.0)
        respuesta.raise_for_status()
        return respuesta.json()
    except httpx.HTTPError as error:
        print(f"Error enviando correo de validacion: {error}")
        return {
            "enviado": False,
            "error": str(error),
        }