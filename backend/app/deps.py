from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import configuracion
from app.database import obtener_db
from app.models import Usuario


esquema_oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/login")


def obtener_usuario_actual(token: str = Depends(esquema_oauth2), db: Session = Depends(obtener_db)) -> Usuario:
    error_credenciales = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        datos_token = jwt.decode(token, configuracion.jwt_secret_key, algorithms=[configuracion.jwt_algorithm])
        sujeto = datos_token.get("sub")
        if sujeto is None:
            raise error_credenciales
        usuario_id = int(sujeto)
    except (JWTError, ValueError):
        raise error_credenciales from None

    usuario = db.get(Usuario, usuario_id)
    if usuario is None or not usuario.is_active:
        raise error_credenciales
    return usuario
