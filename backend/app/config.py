from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Configuracion(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "EV2 Ecommerce Backend"
    environment: str = "local"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/ecommerce"
    jwt_secret_key: str = Field(default="change-me-in-production", min_length=16)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    app_pagos_url: str = "http://app-pagos:8002"
    payment_timeout_seconds: float = 10.0
    cors_origins: str = "http://localhost:4200,http://127.0.0.1:4200,http://localhost:5173"
    auto_create_tables: bool = True
    auto_seed_products: bool = True

    @property
    def lista_origenes_cors(self) -> list[str]:
        return [origen.strip() for origen in self.cors_origins.split(",") if origen.strip()]


configuracion = Configuracion()
