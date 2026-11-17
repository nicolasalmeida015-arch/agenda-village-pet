"""Configurações da aplicação lidas de variáveis de ambiente.

Nenhum segredo fica no código: em produção, DATABASE_URL e JWT_SECRET
são definidos no provedor de hospedagem (ver .env.example).
"""
import os
from dataclasses import dataclass

SEGREDO_DEV = "dev-only-troque-este-segredo-em-producao-32b+"


def normalizar_database_url(url: str) -> str:
    """Provedores (Neon, Render) entregam postgres:// ou postgresql://; o SQLAlchemy usa o driver psycopg 3."""
    for prefixo in ("postgres://", "postgresql://"):
        if url.startswith(prefixo):
            return "postgresql+psycopg://" + url[len(prefixo):]
    return url


@dataclass(frozen=True)
class Settings:
    ambiente: str = os.getenv("AMBIENTE", "desenvolvimento")
    database_url: str = normalizar_database_url(os.getenv("DATABASE_URL", "sqlite:///./agenda.db"))
    jwt_secret: str = os.getenv("JWT_SECRET", SEGREDO_DEV)
    jwt_algorithm: str = "HS256"
    token_minutes_tutor: int = int(os.getenv("TOKEN_MINUTES_TUTOR", "1440"))
    token_minutes_equipe: int = int(os.getenv("TOKEN_MINUTES_EQUIPE", "30"))
    antecedencia_minima_horas: int = int(os.getenv("ANTECEDENCIA_MINIMA_HORAS", "2"))
    max_tentativas_login: int = 5
    janela_bloqueio_minutos: int = 15
    cors_origin: str = os.getenv("CORS_ORIGIN", "*")
    seed_demo: bool = os.getenv("SEED_DEMO", "0") == "1"

    def validar(self) -> None:
        if self.ambiente == "producao" and (self.jwt_secret == SEGREDO_DEV or len(self.jwt_secret) < 32):
            raise RuntimeError("Defina JWT_SECRET (32+ caracteres) no ambiente de produção.")


settings = Settings()
