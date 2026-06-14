from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import obtener_db
from app.deps import obtener_usuario_actual
from app.models import EstadoOrden, EstadoPago, Orden, Usuario
from app.schemas import IntentoPagoLeer, ItemOrdenLeer, OrdenLeer
from app.services.notifications import enviar_email_pago
from app.services.payments import ClientePagos, ErrorServicioPagos

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("/{order_id}", response_model=OrdenLeer)
def obtener_orden(order_id: int, usuario_actual: Usuario = Depends(obtener_usuario_actual), db: Session = Depends(obtener_db)) -> OrdenLeer:
    orden = db.scalar(
        select(Orden)
        .where(Orden.id == order_id, Orden.user_id == usuario_actual.id)
        .options(selectinload(Orden.items), selectinload(Orden.intentos_pago))
    )
    if orden is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Orden no encontrada")

    _sincronizar_pago_pendiente(orden, db)
    return serializar_orden(orden)


def _sincronizar_pago_pendiente(orden: Orden, db: Session) -> None:
    if orden.status != EstadoOrden.pendiente or not orden.intentos_pago:
        return

    ultimo_pago = orden.intentos_pago[-1]

    try:
        estado_app_pagos = ClientePagos().consultar_estado_pago(ultimo_pago.app_pagos_id)
    except ErrorServicioPagos:
        return

    estado_pago = mapear_estado_pago(estado_app_pagos)
    ultimo_pago.status = estado_pago

    if estado_pago == EstadoPago.pagado:
        orden.status = EstadoOrden.pagada
    elif estado_pago in {EstadoPago.rechazado, EstadoPago.expirado, EstadoPago.cancelado}:
        orden.status = EstadoOrden.rechazada

    db.commit()
    db.refresh(orden)

    if estado_pago == EstadoPago.pagado:
        resumen_productos = ", ".join(
            f"{item.product_name} x{item.quantity}"
            for item in orden.items
        )

        resultado_notificacion = enviar_email_pago(
            email=orden.usuario.email,
            nombre_cliente=orden.usuario.full_name,
            identificador_transaccion=str(ultimo_pago.app_pagos_id),
            estado_pago=estado_pago.value,
            fecha_pago=datetime.now(timezone.utc).isoformat(),
            monto_pagado=orden.total,
            resumen_compra=f"Orden #{orden.id}: {resumen_productos}",
        )

        print("Resultado notificacion pago Mercado Pago:", resultado_notificacion)

def mapear_estado_pago(valor_estado: str) -> EstadoPago:
    estado_normalizado = valor_estado.strip().upper()
    if estado_normalizado in {"PAGADO", "PAID", "APPROVED", "APROBADO"}:
        return EstadoPago.pagado
    if estado_normalizado in {"RECHAZADO", "REJECTED", "FAILED", "FAILURE"}:
        return EstadoPago.rechazado
    if estado_normalizado in {"EXPIRADO", "EXPIRED"}:
        return EstadoPago.expirado
    if estado_normalizado in {"CANCELADO", "CANCELLED", "CANCELED"}:
        return EstadoPago.cancelado
    return EstadoPago.pendiente


def serializar_orden(orden: Orden) -> OrdenLeer:
    return OrdenLeer(
        id=orden.id,
        status=orden.status,
        subtotal=orden.subtotal,
        total=orden.total,
        currency=orden.currency,
        items=[
            ItemOrdenLeer(
                id=item.id,
                product_id=item.product_id,
                product_name=item.product_name,
                quantity=item.quantity,
                unit_price=item.unit_price,
                line_total=item.line_total,
            )
            for item in orden.items
        ],
        payment_attempts=[
            IntentoPagoLeer(
                id=pago.id,
                app_pagos_id=pago.app_pagos_id,
                external_reference=pago.external_reference,
                payment_url=pago.payment_url,
                status=pago.status,
                created_at=pago.created_at,
            )
            for pago in orden.intentos_pago
        ],
        created_at=orden.created_at,
        updated_at=orden.updated_at,
    )
