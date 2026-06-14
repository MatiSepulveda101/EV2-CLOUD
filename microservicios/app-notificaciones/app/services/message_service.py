from app.schemas.notifications import WhatsAppArchivoRequest


def enviar_whatsapp_archivo(datos: WhatsAppArchivoRequest) -> dict:
    print("=== NOTIFICACION WHATSAPP/SMS ARCHIVO ===")
    print(f"Telefono: {datos.telefono}")
    print(f"Usuario: {datos.nombre_usuario}")
    print(f"Archivo: {datos.nombre_archivo}")
    print(f"Fecha carga: {datos.fecha_hora_carga}")
    print(f"Espacio utilizado: {datos.espacio_utilizado}")
    print(f"Espacio disponible: {datos.espacio_disponible}")

    return {
        "enviado": True,
        "tipo": "archivo_s3",
        "telefono": datos.telefono,
        "archivo": datos.nombre_archivo,
        "mensaje": "Notificacion de archivo procesada correctamente",
    }