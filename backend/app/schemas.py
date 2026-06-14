from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import EstadoOrden, EstadoPago


class UsuarioCrear(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)


class UsuarioLogin(BaseModel):
    email: EmailStr
    password: str

class UsuarioVerificarCodigo(BaseModel):
    email: EmailStr
    codigo: str = Field(..., min_length=4, max_length=10)


class UsuarioReenviarCodigo(BaseModel):
    email: EmailStr


class UsuarioLeer(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    is_active: bool
    is_verified: bool
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UsuarioLeer


class ProductoLeer(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    price: Decimal
    stock: int
    image_url: str | None = None


class ItemCarritoCrear(BaseModel):
    product_id: int
    quantity: int = Field(..., ge=1, le=99)


class ItemCarritoActualizar(BaseModel):
    quantity: int = Field(..., ge=1, le=99)


class ItemCarritoLeer(BaseModel):
    id: int
    product: ProductoLeer
    quantity: int
    line_total: Decimal


class CarritoLeer(BaseModel):
    id: int
    items: list[ItemCarritoLeer]
    total: Decimal


class RespuestaCheckout(BaseModel):
    order_id: int
    payment_id: str
    payment_url: str
    payment_status: EstadoPago


class ItemOrdenLeer(BaseModel):
    id: int
    product_id: int
    product_name: str
    quantity: int
    unit_price: Decimal
    line_total: Decimal


class IntentoPagoLeer(BaseModel):
    id: int
    app_pagos_id: str
    external_reference: str | None = None
    payment_url: str
    status: EstadoPago
    created_at: datetime


class OrdenLeer(BaseModel):
    id: int
    status: EstadoOrden
    subtotal: Decimal
    total: Decimal
    currency: str
    items: list[ItemOrdenLeer]
    payment_attempts: list[IntentoPagoLeer]
    created_at: datetime
    updated_at: datetime

class ArchivoUsuarioLeer(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    s3_key: str
    content_type: str
    size_bytes: int
    uploaded_at: datetime


class AlmacenamientoUsuarioLeer(BaseModel):
    limite_bytes: int
    usado_bytes: int
    disponible_bytes: int
    usado_mb: float
    disponible_mb: float
    porcentaje_usado: float