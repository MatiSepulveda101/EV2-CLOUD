from __future__ import annotations

from datetime import datetime, timedelta, timezone
import random

from jose import jwt
from passlib.context import CryptContext

from app.config import configuracion


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def generar_hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verificar_password(password_plano: str, password_hasheado: str) -> bool:
    return pwd_context.verify(password_plano, password_hasheado)


def crear_token_acceso(subject: str) -> str:
    expiracion = datetime.now(timezone.utc) + timedelta(minutes=configuracion.access_token_expire_minutes)
    datos_token = {"sub": subject, "exp": expiracion}
    return jwt.encode(datos_token, configuracion.jwt_secret_key, algorithm=configuracion.jwt_algorithm)

def generar_codigo_validacion() -> str:
    return str(random.randint(100000, 999999))


def generar_hash_codigo(codigo: str) -> str:
    return pwd_context.hash(codigo)


def verificar_codigo_validacion(codigo: str, codigo_hasheado: str) -> bool:
    return pwd_context.verify(codigo, codigo_hasheado)