from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import obtener_db
from app.deps import obtener_usuario_actual
from app.models import Carrito, ItemCarrito, Producto, Usuario
from app.schemas import CarritoLeer, ItemCarritoActualizar, ItemCarritoCrear
from app.services.cart import obtener_o_crear_carrito, serializar_carrito


router = APIRouter(prefix="/cart", tags=["cart"])


@router.get("", response_model=CarritoLeer)
def obtener_carrito(usuario_actual: Usuario = Depends(obtener_usuario_actual), db: Session = Depends(obtener_db)) -> CarritoLeer:
    return serializar_carrito(obtener_o_crear_carrito(db, usuario_actual))


@router.post("/items", response_model=CarritoLeer, status_code=status.HTTP_201_CREATED)
def agregar_item_carrito(
    datos: ItemCarritoCrear,
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
    db: Session = Depends(obtener_db),
) -> CarritoLeer:
    producto = _obtener_producto_disponible(db, datos.product_id)
    carrito = obtener_o_crear_carrito(db, usuario_actual)

    item_existente = next((item for item in carrito.items if item.product_id == producto.id), None)
    nueva_cantidad = datos.quantity + (item_existente.quantity if item_existente else 0)
    _asegurar_stock(producto, nueva_cantidad)

    if item_existente is None:
        db.add(ItemCarrito(cart_id=carrito.id, product_id=producto.id, quantity=datos.quantity))
    else:
        item_existente.quantity = nueva_cantidad

    db.commit()
    return serializar_carrito(_recargar_carrito(db, carrito.id))


@router.patch("/items/{item_id}", response_model=CarritoLeer)
def actualizar_item_carrito(
    item_id: int,
    datos: ItemCarritoActualizar,
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
    db: Session = Depends(obtener_db),
) -> CarritoLeer:
    carrito = obtener_o_crear_carrito(db, usuario_actual)
    item = next((item_carrito for item_carrito in carrito.items if item_carrito.id == item_id), None)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item no encontrado en el carrito")

    _asegurar_stock(item.producto, datos.quantity)
    item.quantity = datos.quantity
    db.commit()
    return serializar_carrito(_recargar_carrito(db, carrito.id))


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_item_carrito(
    item_id: int,
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
    db: Session = Depends(obtener_db),
) -> Response:
    carrito = obtener_o_crear_carrito(db, usuario_actual)
    item = next((item_carrito for item_carrito in carrito.items if item_carrito.id == item_id), None)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item no encontrado en el carrito")

    db.delete(item)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _obtener_producto_disponible(db: Session, product_id: int) -> Producto:
    producto = db.get(Producto, product_id)
    if producto is None or not producto.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")
    return producto


def _asegurar_stock(producto: Producto, cantidad: int) -> None:
    if producto.stock < cantidad:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Stock insuficiente")


def _recargar_carrito(db: Session, cart_id: int) -> Carrito:
    return db.scalar(
        select(Carrito)
        .where(Carrito.id == cart_id)
        .options(selectinload(Carrito.items).selectinload(ItemCarrito.producto))
        .execution_options(populate_existing=True)
    )
