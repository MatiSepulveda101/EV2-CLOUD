from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Carrito, ItemCarrito, Usuario
from app.schemas import CarritoLeer, ItemCarritoLeer, ProductoLeer


def obtener_o_crear_carrito(db: Session, usuario: Usuario) -> Carrito:
    carrito = db.scalar(
        select(Carrito)
        .where(Carrito.user_id == usuario.id)
        .options(selectinload(Carrito.items).selectinload(ItemCarrito.producto))
    )
    if carrito is not None:
        return carrito

    carrito = Carrito(user_id=usuario.id)
    db.add(carrito)
    db.commit()
    db.refresh(carrito)
    return db.scalar(
        select(Carrito)
        .where(Carrito.id == carrito.id)
        .options(selectinload(Carrito.items).selectinload(ItemCarrito.producto))
    )


def calcular_total_carrito(carrito: Carrito) -> Decimal:
    return sum((item.producto.price * item.quantity for item in carrito.items), Decimal("0"))


def serializar_carrito(carrito: Carrito) -> CarritoLeer:
    return CarritoLeer(
        id=carrito.id,
        items=[
            ItemCarritoLeer(
                id=item.id,
                product=ProductoLeer.model_validate(item.producto),
                quantity=item.quantity,
                line_total=item.producto.price * item.quantity,
            )
            for item in carrito.items
        ],
        total=calcular_total_carrito(carrito),
    )
