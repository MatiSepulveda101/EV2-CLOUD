from __future__ import annotations

import html
import os
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr

from app.schemas.notifications import (
    EmailCompraRequest,
    EmailPagoRequest,
    EmailValidacionRequest,
)


SMTP_HOST = os.getenv("SMTP_HOST", "").strip()
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "").strip()
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "").strip() or SMTP_USER
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "EV2 Cloud").strip()
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").strip().lower() in {"1", "true", "yes"}
SMTP_USE_SSL = os.getenv("SMTP_USE_SSL", "false").strip().lower() in {"1", "true", "yes"}


def _formatear_clp(valor: float) -> str:
    return f"${valor:,.0f}".replace(",", ".")


def _enviar_email(destinatario: str, asunto: str, texto: str, contenido_html: str) -> dict:
    if not SMTP_HOST or not SMTP_FROM:
        return {
            "enviado": False,
            "destinatario": destinatario,
            "error": "SMTP_HOST y SMTP_FROM deben estar configurados",
        }

    mensaje = EmailMessage()
    mensaje["Subject"] = asunto
    mensaje["From"] = formataddr((SMTP_FROM_NAME, SMTP_FROM))
    mensaje["To"] = destinatario
    mensaje.set_content(texto)
    mensaje.add_alternative(contenido_html, subtype="html")

    if SMTP_USE_SSL:
        contexto = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context, timeout=15) as servidor:
            if SMTP_USER:
                servidor.login(SMTP_USER, SMTP_PASSWORD)
            servidor.send_message(mensaje)
    else:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as servidor:
            servidor.ehlo()
            if SMTP_USE_TLS:
                servidor.starttls(context=ssl.create_default_context())
                servidor.ehlo()
            if SMTP_USER:
                servidor.login(SMTP_USER, SMTP_PASSWORD)
            servidor.send_message(mensaje)

    return {
        "enviado": True,
        "destinatario": destinatario,
        "mensaje": "Correo enviado correctamente",
    }


def _plantilla(titulo: str, cuerpo: str) -> str:
    return f"""\
<!doctype html>
<html lang="es">
  <body style="margin:0;background:#f4f6f8;font-family:Arial,sans-serif;color:#1f2937">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
      <tr>
        <td align="center" style="padding:32px 16px">
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0"
                 style="max-width:680px;background:#ffffff;border-radius:12px;overflow:hidden">
            <tr>
              <td style="background:#111827;color:#ffffff;padding:24px 32px">
                <div style="font-size:14px;letter-spacing:1px">{html.escape(SMTP_FROM_NAME)}</div>
                <h1 style="margin:8px 0 0;font-size:26px">{titulo}</h1>
              </td>
            </tr>
            <tr>
              <td style="padding:30px 32px">{cuerpo}</td>
            </tr>
            <tr>
              <td style="padding:20px 32px;background:#f9fafb;color:#6b7280;font-size:12px">
                Este correo fue generado automaticamente. Conserva esta boleta como respaldo.
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
"""


def enviar_correo_validacion(datos: EmailValidacionRequest) -> dict:
    nombre = html.escape(datos.nombre)
    codigo = html.escape(datos.codigo)
    cuerpo = f"""
      <p>Hola {nombre},</p>
      <p>Usa el siguiente codigo para validar tu cuenta:</p>
      <p style="font-size:28px;font-weight:bold;letter-spacing:4px">{codigo}</p>
    """
    resultado = _enviar_email(
        datos.email,
        "Codigo de validacion de cuenta",
        f"Hola {datos.nombre}. Tu codigo de validacion es {datos.codigo}.",
        _plantilla("Valida tu cuenta", cuerpo),
    )
    return {**resultado, "tipo": "validacion_cuenta"}


def enviar_correo_compra(datos: EmailCompraRequest) -> dict:
    filas_html = []
    filas_texto = []

    for producto in datos.productos:
        nombre = html.escape(producto.nombre)
        filas_html.append(
            f"""
            <tr>
              <td style="padding:12px;border-bottom:1px solid #e5e7eb">{nombre}</td>
              <td align="center" style="padding:12px;border-bottom:1px solid #e5e7eb">{producto.cantidad}</td>
              <td align="right" style="padding:12px;border-bottom:1px solid #e5e7eb">
                {_formatear_clp(producto.precio_unitario)}
              </td>
              <td align="right" style="padding:12px;border-bottom:1px solid #e5e7eb">
                {_formatear_clp(producto.total)}
              </td>
            </tr>
            """
        )
        filas_texto.append(
            f"{producto.nombre} x{producto.cantidad}: {_formatear_clp(producto.total)}"
        )

    numero_compra = html.escape(datos.numero_compra)
    nombre_cliente = html.escape(datos.nombre_cliente)
    fecha_compra = html.escape(datos.fecha_compra)
    total = _formatear_clp(datos.total_pagado)
    cuerpo = f"""
      <p>Hola {nombre_cliente},</p>
      <p>Tu pago fue confirmado. A continuacion encontraras la boleta y el detalle de tu compra.</p>
      <table role="presentation" width="100%" cellspacing="0" cellpadding="0"
             style="margin:24px 0;border:1px solid #e5e7eb;border-radius:8px">
        <tr>
          <td style="padding:12px"><strong>Boleta</strong></td>
          <td align="right" style="padding:12px">#{numero_compra}</td>
        </tr>
        <tr>
          <td style="padding:12px"><strong>Fecha</strong></td>
          <td align="right" style="padding:12px">{fecha_compra}</td>
        </tr>
      </table>
      <table role="presentation" width="100%" cellspacing="0" cellpadding="0"
             style="border-collapse:collapse">
        <thead>
          <tr style="background:#f3f4f6">
            <th align="left" style="padding:12px">Producto</th>
            <th style="padding:12px">Cantidad</th>
            <th align="right" style="padding:12px">Precio</th>
            <th align="right" style="padding:12px">Subtotal</th>
          </tr>
        </thead>
        <tbody>{''.join(filas_html)}</tbody>
        <tfoot>
          <tr>
            <td colspan="3" align="right" style="padding:16px;font-size:18px"><strong>Total pagado</strong></td>
            <td align="right" style="padding:16px;font-size:18px"><strong>{total}</strong></td>
          </tr>
        </tfoot>
      </table>
    """
    texto = "\n".join(
        [
            f"Boleta de compra #{datos.numero_compra}",
            f"Cliente: {datos.nombre_cliente}",
            f"Fecha: {datos.fecha_compra}",
            "",
            *filas_texto,
            "",
            f"Total pagado: {total}",
        ]
    )
    resultado = _enviar_email(
        datos.email,
        f"Boleta de compra #{datos.numero_compra}",
        texto,
        _plantilla("Compra confirmada", cuerpo),
    )
    return {**resultado, "tipo": "compra", "numero_compra": datos.numero_compra}


def enviar_correo_pago(datos: EmailPagoRequest) -> dict:
    cuerpo = f"""
      <p>Hola {html.escape(datos.nombre_cliente)},</p>
      <p>El estado de tu pago es <strong>{html.escape(datos.estado_pago)}</strong>.</p>
      <p><strong>Transaccion:</strong> {html.escape(datos.identificador_transaccion)}</p>
      <p><strong>Fecha:</strong> {html.escape(datos.fecha_pago)}</p>
      <p><strong>Monto:</strong> {_formatear_clp(datos.monto_pagado)}</p>
      <p>{html.escape(datos.resumen_compra)}</p>
    """
    resultado = _enviar_email(
        datos.email,
        f"Confirmacion de pago #{datos.identificador_transaccion}",
        (
            f"Pago {datos.estado_pago}. Transaccion {datos.identificador_transaccion}. "
            f"Monto {_formatear_clp(datos.monto_pagado)}."
        ),
        _plantilla("Confirmacion de pago", cuerpo),
    )
    return {
        **resultado,
        "tipo": "pago_mercado_pago",
        "transaccion": datos.identificador_transaccion,
        "estado_pago": datos.estado_pago,
    }
