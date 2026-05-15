from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

import httpx

from app.config import configuracion


class ErrorServicioPagos(RuntimeError):
    pass


@dataclass(frozen=True)
class CheckoutPago:
    app_pagos_id: str
    payment_url: str
    external_reference: str | None
    raw_response: dict[str, Any]


class ClientePagos:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or configuracion.app_pagos_url).rstrip("/")

    def crear_checkout(self, usuario_id: int, email: str, descripcion: str, monto: Decimal) -> CheckoutPago:
        datos_pago = {
            "id_usuario": usuario_id,
            "email_pagador": email,
            "descripcion": descripcion,
            "monto": float(monto),
        }
        respuesta = self._enviar_peticion("POST", "/pagos/crear", json=datos_pago)
        datos_checkout = respuesta.get("data") if isinstance(respuesta.get("data"), dict) else respuesta

        app_pagos_id = datos_checkout.get("id_pago") or datos_checkout.get("payment_id") or datos_checkout.get("id")
        payment_url = datos_checkout.get("url_pago") or datos_checkout.get("payment_url") or datos_checkout.get("init_point")
        external_reference = datos_checkout.get("external_reference") or datos_checkout.get("referencia_externa")

        if not app_pagos_id or not payment_url:
            raise ErrorServicioPagos("El microservicio de pagos no retorno id_pago o url_pago")

        return CheckoutPago(
            app_pagos_id=str(app_pagos_id),
            payment_url=str(payment_url),
            external_reference=str(external_reference) if external_reference else None,
            raw_response=respuesta,
        )

    def consultar_estado_pago(self, app_pagos_id: str) -> str:
        respuesta = self._enviar_peticion("GET", f"/pagos/{app_pagos_id}/estado")
        estado = respuesta.get("estado") or respuesta.get("status") or respuesta.get("payment_status")
        if not estado:
            raise ErrorServicioPagos("El microservicio de pagos no retorno estado")
        return str(estado)

    def _enviar_peticion(self, metodo: str, ruta: str, **kwargs: Any) -> dict[str, Any]:
        url = f"{self.base_url}{ruta}"
        try:
            with httpx.Client(timeout=configuracion.payment_timeout_seconds) as cliente_http:
                respuesta = cliente_http.request(metodo, url, **kwargs)
                respuesta.raise_for_status()
                datos = respuesta.json()
        except httpx.HTTPStatusError as exc:
            raise ErrorServicioPagos(f"Error HTTP desde app-pagos: {exc.response.status_code}") from exc
        except (httpx.HTTPError, ValueError) as exc:
            raise ErrorServicioPagos("No fue posible comunicarse con app-pagos") from exc

        if not isinstance(datos, dict):
            raise ErrorServicioPagos("Respuesta invalida desde app-pagos")
        return datos
