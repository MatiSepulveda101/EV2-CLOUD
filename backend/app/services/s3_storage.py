from __future__ import annotations

from io import BytesIO
from uuid import uuid4

import boto3
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError
from fastapi import HTTPException, status

from app.config import configuracion


def _cliente_s3():
    if not configuracion.s3_bucket_name:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Bucket S3 no configurado",
        )

    return boto3.client(
        "s3",
        region_name=configuracion.aws_region,
        aws_access_key_id=configuracion.aws_access_key_id,
        aws_secret_access_key=configuracion.aws_secret_access_key,
    )


def generar_s3_key(user_id: int, filename: str) -> str:
    nombre_limpio = filename.replace("\\", "_").replace("/", "_")
    identificador = uuid4().hex
    return f"usuarios/{user_id}/{identificador}_{nombre_limpio}"


def subir_bytes_s3(
    user_id: int,
    filename: str,
    content_type: str,
    contenido: bytes,
) -> str:
    s3_key = generar_s3_key(user_id, filename)

    try:
        cliente = _cliente_s3()
        cliente.upload_fileobj(
            BytesIO(contenido),
            configuracion.s3_bucket_name,
            s3_key,
            ExtraArgs={
                "ContentType": content_type or "application/octet-stream"
            },
        )
    except NoCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Credenciales AWS no configuradas",
        )
    except (BotoCoreError, ClientError) as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error subiendo archivo a S3: {error}",
        )

    return s3_key