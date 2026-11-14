"""Configurações da aplicação lidas de variáveis de ambiente.

Nenhum segredo fica no código: em produção, DATABASE_URL e JWT_SECRET
são definidos no provedor de hospedagem (ver .env.example).
"""
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./agenda.db")
    jwt_secret: str = os.getenv("JWT_SECRET", "dev-only-troque-este-segredo-em-producao-32b+")
    jwt_algorithm: str = "HS256"
    token_minutes_tutor: int = int(os.getenv("TOKEN_MINUTES_TUTOR", "1440"))
    token_minutes_equipe: int = int(os.getenv("TOKEN_MINUTES_EQUIPE", "30"))
    antecedencia_minima_horas: int = int(os.getenv("ANTECEDENCIA_MINIMA_HORAS", "2"))
    max_tentativas_login: int = 5
    janela_bloqueio_minutos: int = 15
    cors_origin: str = os.getenv("CORS_ORIGIN", "*")


settings = Settings()
