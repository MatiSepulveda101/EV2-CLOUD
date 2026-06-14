from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Configuracion(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    app_name: str = "EV2 Ecommerce Backend"
    environment: str = "local"

    DB_HOST: str = "localhost"
    DB_PORT: str = "5432"
    DB_NAME: str = "ecommerce"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"

    jwt_secret_key: str = Field(
        default="change-me-in-production",
        min_length=16
    )

    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    app_pagos_url: str = "http://app-pagos:8002"
    payment_timeout_seconds: float = 10.0
    notifications_service_url: str = "http://app-notificaciones:8003"

    cors_origins: str = (
        "http://localhost:4200,"
        "http://127.0.0.1:4200,"
        "http://localhost:5173,"
        "http://ev2-alb-873341758.us-east-1.elb.amazonaws.com"
    )

    auto_create_tables: bool = True
    auto_seed_products: bool = True

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def lista_origenes_cors(self) -> list[str]:
        return [
            origen.strip()
            for origen in self.cors_origins.split(",")
            if origen.strip()
        ]


configuracion = Configuracion()
