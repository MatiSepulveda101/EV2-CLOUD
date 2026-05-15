from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import obtener_db
from app.models import Producto
from app.schemas import ProductoLeer


router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[ProductoLeer])
def listar_productos(db: Session = Depends(obtener_db)) -> list[Producto]:
    return list(db.scalars(select(Producto).where(Producto.is_active.is_(True)).order_by(Producto.id)))


@router.get("/{product_id}", response_model=ProductoLeer)
def obtener_producto(product_id: int, db: Session = Depends(obtener_db)) -> Producto:
    producto = db.get(Producto, product_id)
    if producto is None or not producto.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")
    return producto
