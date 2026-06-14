from pydantic import BaseModel, EmailStr, Field


class ProductoCompra(BaseModel):
    nombre: str
    cantidad: int
    precio_unitario: float
    total: float


class EmailValidacionRequest(BaseModel):
    email: EmailStr
    nombre: str
    codigo: str = Field(..., min_length=4, max_length=10)


class EmailCompraRequest(BaseModel):
    email: EmailStr
    nombre_cliente: str
    numero_compra: str
    fecha_compra: str
    productos: list[ProductoCompra]
    total_pagado: float


class EmailPagoRequest(BaseModel):
    email: EmailStr
    nombre_cliente: str
    identificador_transaccion: str
    estado_pago: str
    fecha_pago: str
    monto_pagado: float
    resumen_compra: str


class WhatsAppArchivoRequest(BaseModel):
    telefono: str
    nombre_usuario: str
    nombre_archivo: str
    fecha_hora_carga: str
    espacio_utilizado: str
    espacio_disponible: str