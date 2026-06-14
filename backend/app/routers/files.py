from __future__ import annotations

from datetime import timezone

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import configuracion
from app.database import obtener_db
from app.deps import obtener_usuario_actual
from app.models import ArchivoUsuario, Usuario
from app.schemas import AlmacenamientoUsuarioLeer, ArchivoUsuarioLeer
from app.services.notifications import enviar_notificacion_archivo
from app.services.s3_storage import subir_bytes_s3


router = APIRouter(prefix="/files", tags=["files"])


def _obtener_espacio_usado(db: Session, user_id: int) -> int:
    resultado = db.scalar(
        select(func.coalesce(func.sum(ArchivoUsuario.size_bytes), 0)).where(
            ArchivoUsuario.user_id == user_id
        )
    )
    return int(resultado or 0)


def _bytes_a_mb(valor: int) -> float:
    return round(valor / 1024 / 1024, 2)


def _formato_bytes(valor: int) -> str:
    mb = valor / 1024 / 1024

    if mb < 1024:
        return f"{mb:.2f} MB"

    gb = mb / 1024
    return f"{gb:.2f} GB"


@router.post("/upload", response_model=ArchivoUsuarioLeer, status_code=status.HTTP_201_CREATED)
async def subir_archivo(
    archivo: UploadFile = File(...),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
    db: Session = Depends(obtener_db),
) -> ArchivoUsuario:
    if not archivo.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo debe tener nombre",
        )

    contenido = await archivo.read()
    size_bytes = len(contenido)

    if size_bytes <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo esta vacio",
        )

    limite = int(configuracion.user_storage_limit_bytes)
    usado_actual = _obtener_espacio_usado(db, usuario_actual.id)

    if usado_actual + size_bytes > limite:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="No tienes espacio suficiente para subir este archivo",
        )

    s3_key = subir_bytes_s3(
        user_id=usuario_actual.id,
        filename=archivo.filename,
        content_type=archivo.content_type or "application/octet-stream",
        contenido=contenido,
    )

    registro = ArchivoUsuario(
        user_id=usuario_actual.id,
        filename=archivo.filename,
        s3_key=s3_key,
        content_type=archivo.content_type or "application/octet-stream",
        size_bytes=size_bytes,
    )

    db.add(registro)
    db.commit()
    db.refresh(registro)

    usado_final = usado_actual + size_bytes
    disponible_final = limite - usado_final

    resultado_notificacion = enviar_notificacion_archivo(
        telefono="sin-telefono-configurado",
        nombre_usuario=usuario_actual.full_name,
        nombre_archivo=registro.filename,
        fecha_hora_carga=registro.uploaded_at.astimezone(timezone.utc).isoformat(),
        espacio_utilizado=_formato_bytes(usado_final),
        espacio_disponible=_formato_bytes(disponible_final),
    )

    print("Resultado notificacion archivo:", resultado_notificacion)

    return registro


@router.get("", response_model=list[ArchivoUsuarioLeer])
def listar_archivos(
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
    db: Session = Depends(obtener_db),
) -> list[ArchivoUsuario]:
    return list(
        db.scalars(
            select(ArchivoUsuario)
            .where(ArchivoUsuario.user_id == usuario_actual.id)
            .order_by(ArchivoUsuario.uploaded_at.desc())
        )
    )


@router.get("/storage", response_model=AlmacenamientoUsuarioLeer)
def obtener_almacenamiento(
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
    db: Session = Depends(obtener_db),
) -> AlmacenamientoUsuarioLeer:
    limite = int(configuracion.user_storage_limit_bytes)
    usado = _obtener_espacio_usado(db, usuario_actual.id)
    disponible = max(limite - usado, 0)

    porcentaje = 0.0
    if limite > 0:
        porcentaje = round((usado / limite) * 100, 2)

    return AlmacenamientoUsuarioLeer(
        limite_bytes=limite,
        usado_bytes=usado,
        disponible_bytes=disponible,
        usado_mb=_bytes_a_mb(usado),
        disponible_mb=_bytes_a_mb(disponible),
        porcentaje_usado=porcentaje,
    )