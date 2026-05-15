from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import obtener_db
from app.models import Carrito, Usuario
from app.schemas import Token, UsuarioCrear, UsuarioLeer, UsuarioLogin
from app.security import crear_token_acceso, generar_hash_password, verificar_password


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UsuarioLeer, status_code=status.HTTP_201_CREATED)
def registrar_usuario(datos: UsuarioCrear, db: Session = Depends(obtener_db)) -> Usuario:
    usuario_existente = db.scalar(select(Usuario).where(Usuario.email == datos.email.lower()))
    if usuario_existente is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El email ya esta registrado")

    usuario = Usuario(
        email=datos.email.lower(),
        full_name=datos.full_name,
        hashed_password=generar_hash_password(datos.password),
    )
    db.add(usuario)
    db.flush()
    db.add(Carrito(user_id=usuario.id))
    db.commit()
    db.refresh(usuario)
    return usuario


@router.post("/login", response_model=Token)
async def iniciar_sesion(request: Request, db: Session = Depends(obtener_db)) -> Token:
    datos = await _leer_datos_login(request)
    usuario = db.scalar(select(Usuario).where(Usuario.email == datos.email.lower()))
    if usuario is None or not verificar_password(datos.password, usuario.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email o password incorrecto")

    token = crear_token_acceso(subject=str(usuario.id))
    return Token(access_token=token, user=UsuarioLeer.model_validate(usuario))


async def _leer_datos_login(request: Request) -> UsuarioLogin:
    content_type = request.headers.get("content-type", "")
    if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
        form = await request.form()
        return UsuarioLogin(email=str(form.get("username") or form.get("email")), password=str(form.get("password")))

    body = await request.json()
    return UsuarioLogin.model_validate(body)
