from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import obtener_db
from app.models import Carrito, Usuario
from app.schemas import (
    Token,
    UsuarioCrear,
    UsuarioLeer,
    UsuarioLogin,
    UsuarioReenviarCodigo,
    UsuarioVerificarCodigo,
)
from app.security import (
    crear_token_acceso,
    generar_codigo_validacion,
    generar_hash_codigo,
    generar_hash_password,
    verificar_codigo_validacion,
    verificar_password,
)
from app.services.notifications import enviar_email_validacion


router = APIRouter(prefix="/auth", tags=["auth"])

MINUTOS_EXPIRACION_CODIGO = 15


def _fecha_actual_utc() -> datetime:
    return datetime.now(timezone.utc)


def _normalizar_fecha(fecha: datetime | None) -> datetime | None:
    if fecha is None:
        return None
    if fecha.tzinfo is None:
        return fecha.replace(tzinfo=timezone.utc)
    return fecha


def _generar_y_asignar_codigo(usuario: Usuario) -> str:
    codigo = generar_codigo_validacion()
    usuario.verification_code_hash = generar_hash_codigo(codigo)
    usuario.verification_code_expires_at = _fecha_actual_utc() + timedelta(minutes=MINUTOS_EXPIRACION_CODIGO)
    return codigo


@router.post("/register", response_model=UsuarioLeer, status_code=status.HTTP_201_CREATED)
def registrar_usuario(datos: UsuarioCrear, db: Session = Depends(obtener_db)) -> Usuario:
    usuario_existente = db.scalar(select(Usuario).where(Usuario.email == datos.email.lower()))
    if usuario_existente is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El email ya esta registrado")

    usuario = Usuario(
        email=datos.email.lower(),
        full_name=datos.full_name,
        hashed_password=generar_hash_password(datos.password),
        is_verified=False,
    )

    codigo = _generar_y_asignar_codigo(usuario)

    db.add(usuario)
    db.flush()
    db.add(Carrito(user_id=usuario.id))
    db.commit()
    db.refresh(usuario)

    resultado_notificacion = enviar_email_validacion(
        email=usuario.email,
        nombre=usuario.full_name,
        codigo=codigo,
    )

    print("Resultado notificacion validacion:", resultado_notificacion)

    return usuario


@router.post("/verify", response_model=UsuarioLeer)
def verificar_cuenta(datos: UsuarioVerificarCodigo, db: Session = Depends(obtener_db)) -> Usuario:
    usuario = db.scalar(select(Usuario).where(Usuario.email == datos.email.lower()))

    if usuario is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    if usuario.is_verified:
        return usuario

    if not usuario.verification_code_hash:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No existe codigo de validacion activo")

    fecha_expiracion = _normalizar_fecha(usuario.verification_code_expires_at)

    if fecha_expiracion is None or fecha_expiracion < _fecha_actual_utc():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El codigo de validacion expiro")

    codigo_correcto = verificar_codigo_validacion(
        datos.codigo,
        usuario.verification_code_hash,
    )

    if not codigo_correcto:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Codigo de validacion incorrecto")

    usuario.is_verified = True
    usuario.verified_at = _fecha_actual_utc()
    usuario.verification_code_hash = None
    usuario.verification_code_expires_at = None

    db.commit()
    db.refresh(usuario)

    return usuario


@router.post("/resend-code")
def reenviar_codigo(datos: UsuarioReenviarCodigo, db: Session = Depends(obtener_db)) -> dict:
    usuario = db.scalar(select(Usuario).where(Usuario.email == datos.email.lower()))

    if usuario is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    if usuario.is_verified:
        return {
            "message": "La cuenta ya se encuentra validada",
            "email": usuario.email,
        }

    codigo = _generar_y_asignar_codigo(usuario)
    db.commit()
    db.refresh(usuario)

    resultado_notificacion = enviar_email_validacion(
        email=usuario.email,
        nombre=usuario.full_name,
        codigo=codigo,
    )

    return {
        "message": "Codigo reenviado correctamente",
        "email": usuario.email,
        "notificacion": resultado_notificacion,
    }


@router.post("/login", response_model=Token)
async def iniciar_sesion(request: Request, db: Session = Depends(obtener_db)) -> Token:
    datos = await _leer_datos_login(request)
    usuario = db.scalar(select(Usuario).where(Usuario.email == datos.email.lower()))

    if usuario is None or not verificar_password(datos.password, usuario.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email o password incorrecto")

    if not usuario.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Debes validar tu cuenta antes de iniciar sesion",
        )

    token = crear_token_acceso(subject=str(usuario.id))
    return Token(access_token=token, user=UsuarioLeer.model_validate(usuario))


async def _leer_datos_login(request: Request) -> UsuarioLogin:
    content_type = request.headers.get("content-type", "")

    if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
        form = await request.form()
        return UsuarioLogin(email=str(form.get("username") or form.get("email")), password=str(form.get("password")))

    body = await request.json()
    return UsuarioLogin.model_validate(body)