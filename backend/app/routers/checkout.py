from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import obtener_db
from app.deps import obtener_usuario_actual
from app.models import EstadoPago, IntentoPago, ItemOrden, Orden, Usuario
from app.schemas import RespuestaCheckout
from app.services.cart import calcular_total_carrito, obtener_o_crear_carrito
from app.services.payments import ClientePagos, ErrorServicioPagos


router = APIRouter(prefix="/checkout", tags=["checkout"])


@router.post("", response_model=RespuestaCheckout, status_code=status.HTTP_201_CREATED)
def crear_checkout_orden(usuario_actual: Usuario = Depends(obtener_usuario_actual), db: Session = Depends(obtener_db)) -> RespuestaCheckout:
    carrito = obtener_o_crear_carrito(db, usuario_actual)
    if not carrito.items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El carrito esta vacio")

    for item in carrito.items:
        if item.producto.stock < item.quantity:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Stock insuficiente para {item.producto.name}",
            )

    total = calcular_total_carrito(carrito)
    orden = Orden(user_id=usuario_actual.id, subtotal=total, total=total)
    db.add(orden)
    db.flush()

    for item in carrito.items:
        db.add(
            ItemOrden(
                order_id=orden.id,
                product_id=item.product_id,
                product_name=item.producto.name,
                quantity=item.quantity,
                unit_price=item.producto.price,
                line_total=item.producto.price * item.quantity,
            )
        )

    db.commit()
    db.refresh(orden)

    try:
        checkout = ClientePagos().crear_checkout(
            usuario_id=usuario_actual.id,
            email=usuario_actual.email,
            descripcion=f"Orden #{orden.id}",
            monto=total,
        )
    except ErrorServicioPagos as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    pago = IntentoPago(
        order_id=orden.id,
        app_pagos_id=checkout.app_pagos_id,
        external_reference=checkout.external_reference,
        payment_url=checkout.payment_url,
        status=EstadoPago.pendiente,
        provider_response=checkout.raw_response,
    )
    db.add(pago)
    db.commit()

    return RespuestaCheckout(
        order_id=orden.id,
        payment_id=pago.app_pagos_id,
        payment_url=pago.payment_url,
        payment_status=pago.status,
    )
