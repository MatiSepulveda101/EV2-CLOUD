from __future__ import annotations

import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, JSON, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class EstadoOrden(str, enum.Enum):
    pendiente = "PENDING"
    pagada = "PAID"
    rechazada = "REJECTED"
    cancelada = "CANCELLED"


class EstadoPago(str, enum.Enum):
    pendiente = "PENDING"
    pagado = "PAID"
    rechazado = "REJECTED"
    expirado = "EXPIRED"
    cancelado = "CANCELLED"


class Usuario(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    carrito: Mapped["Carrito"] = relationship(back_populates="usuario", cascade="all, delete-orphan", uselist=False)
    ordenes: Mapped[list["Orden"]] = relationship(back_populates="usuario")


class Producto(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    items_carrito: Mapped[list["ItemCarrito"]] = relationship(back_populates="producto")
    items_orden: Mapped[list["ItemOrden"]] = relationship(back_populates="producto")


class Carrito(Base):
    __tablename__ = "carts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    usuario: Mapped[Usuario] = relationship(back_populates="carrito")
    items: Mapped[list["ItemCarrito"]] = relationship(back_populates="carrito", cascade="all, delete-orphan")


class ItemCarrito(Base):
    __tablename__ = "cart_items"
    __table_args__ = (UniqueConstraint("cart_id", "product_id", name="uq_cart_product"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    cart_id: Mapped[int] = mapped_column(ForeignKey("carts.id"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False, index=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    carrito: Mapped[Carrito] = relationship(back_populates="items")
    producto: Mapped[Producto] = relationship(back_populates="items_carrito")


class Orden(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    status: Mapped[EstadoOrden] = mapped_column(
        Enum(EstadoOrden, name="order_status", native_enum=False),
        default=EstadoOrden.pendiente,
        nullable=False,
    )
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="CLP", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    usuario: Mapped[Usuario] = relationship(back_populates="ordenes")
    items: Mapped[list["ItemOrden"]] = relationship(back_populates="orden", cascade="all, delete-orphan")
    intentos_pago: Mapped[list["IntentoPago"]] = relationship(back_populates="orden", cascade="all, delete-orphan")


class ItemOrden(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False, index=True)
    product_name: Mapped[str] = mapped_column(String(180), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    orden: Mapped[Orden] = relationship(back_populates="items")
    producto: Mapped[Producto] = relationship(back_populates="items_orden")


class IntentoPago(Base):
    __tablename__ = "payment_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False, index=True)
    app_pagos_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    external_reference: Mapped[str | None] = mapped_column(String(160), nullable=True, index=True)
    payment_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    status: Mapped[EstadoPago] = mapped_column(
        Enum(EstadoPago, name="payment_status", native_enum=False),
        default=EstadoPago.pendiente,
        nullable=False,
    )
    provider_response: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    orden: Mapped[Orden] = relationship(back_populates="intentos_pago")
