from app.schemas.notifications import (
    EmailCompraRequest,
    EmailPagoRequest,
    EmailValidacionRequest,
)


def enviar_correo_validacion(datos: EmailValidacionRequest) -> dict:
    print("=== CORREO DE VALIDACION ===")
    print(f"Para: {datos.email}")
    print(f"Nombre: {datos.nombre}")
    print(f"Codigo: {datos.codigo}")

    return {
        "enviado": True,
        "tipo": "validacion_cuenta",
        "destinatario": datos.email,
        "mensaje": "Correo de validacion procesado correctamente",
    }


def enviar_correo_compra(datos: EmailCompraRequest) -> dict:
    print("=== CORREO DE COMPRA ===")
    print(f"Para: {datos.email}")
    print(f"Cliente: {datos.nombre_cliente}")
    print(f"Compra: {datos.numero_compra}")
    print(f"Fecha: {datos.fecha_compra}")
    print(f"Total: {datos.total_pagado}")

    for producto in datos.productos:
        print(f"- {producto.nombre} x{producto.cantidad} = {producto.total}")

    return {
        "enviado": True,
        "tipo": "compra",
        "destinatario": datos.email,
        "numero_compra": datos.numero_compra,
        "mensaje": "Correo de compra procesado correctamente",
    }


def enviar_correo_pago(datos: EmailPagoRequest) -> dict:
    print("=== CORREO DE PAGO MERCADO PAGO ===")
    print(f"Para: {datos.email}")
    print(f"Cliente: {datos.nombre_cliente}")
    print(f"Transaccion: {datos.identificador_transaccion}")
    print(f"Estado: {datos.estado_pago}")
    print(f"Fecha pago: {datos.fecha_pago}")
    print(f"Monto: {datos.monto_pagado}")

    return {
        "enviado": True,
        "tipo": "pago_mercado_pago",
        "destinatario": datos.email,
        "transaccion": datos.identificador_transaccion,
        "estado_pago": datos.estado_pago,
        "mensaje": "Correo de pago procesado correctamente",
    }