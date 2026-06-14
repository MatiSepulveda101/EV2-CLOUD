from __future__ import annotations

from decimal import Decimal
from typing import Any

import httpx

from app.config import configuracion


def _post_notificacion(ruta: str, payload: dict[str, Any]) -> dict[str, Any]:
    url = f"{configuracion.notifications_service_url.rstrip('/')}{ruta}"

    try:
        respuesta = httpx.post(url, json=payload, timeout=5.0)
        respuesta.raise_for_status()
        return respuesta.json()
    except httpx.HTTPError as error:
        print(f"Error enviando notificacion a {ruta}: {error}")
        return {
            "enviado": False,
            "error": str(error),
            "ruta": ruta,
        }


def _decimal_a_float(valor: Decimal | int | float) -> float:
    return float(valor)


def enviar_email_validacion(email: str, nombre: str, codigo: str) -> dict[str, Any]:
    payload = {
        "email": email,
        "nombre": nombre,
        "codigo": codigo,
    }

    return _post_notificacion("/notificaciones/email/validacion", payload)


def enviar_email_compra(
    email: str,
    nombre_cliente: str,
    numero_compra: str,
    fecha_compra: str,
    productos: list[dict[str, Any]],
    total_pagado: Decimal | int | float,
) -> dict[str, Any]:
    payload = {
        "email": email,
        "nombre_cliente": nombre_cliente,
        "numero_compra": numero_compra,
        "fecha_compra": fecha_compra,
        "productos": productos,
        "total_pagado": _decimal_a_float(total_pagado),
    }

    return _post_notificacion("/notificaciones/email/compra", payload)


def enviar_email_pago(
    email: str,
    nombre_cliente: str,
    identificador_transaccion: str,
    estado_pago: str,
    fecha_pago: str,
    monto_pagado: Decimal | int | float,
    resumen_compra: str,
) -> dict[str, Any]:
    payload = {
        "email": email,
        "nombre_cliente": nombre_cliente,
        "identificador_transaccion": identificador_transaccion,
        "estado_pago": estado_pago,
        "fecha_pago": fecha_pago,
        "monto_pagado": _decimal_a_float(monto_pagado),
        "resumen_compra": resumen_compra,
    }

    return _post_notificacion("/notificaciones/email/pago", payload)

def enviar_notificacion_archivo(
    telefono: str,
    nombre_usuario: str,
    nombre_archivo: str,
    fecha_hora_carga: str,
    espacio_utilizado: str,
    espacio_disponible: str,
) -> dict[str, Any]:
    payload = {
        "telefono": telefono,
        "nombre_usuario": nombre_usuario,
        "nombre_archivo": nombre_archivo,
        "fecha_hora_carga": fecha_hora_carga,
        "espacio_utilizado": espacio_utilizado,
        "espacio_disponible": espacio_disponible,
    }

    return _post_notificacion("/notificaciones/whatsapp/archivo", payload)