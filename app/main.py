"""Ponto de entrada da API Agenda Village Pet."""
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import Base, engine
from app.routers import auth, tutor

log = logging.getLogger("app")


def create_app() -> FastAPI:
    Base.metadata.create_all(bind=engine)
    app = FastAPI(title="Agenda Village Pet", version="0.3.0",
                  description="MVP de agendamento de banho e tosa - Village Pet BR-116")
    app.add_middleware(CORSMiddleware, allow_origins=[settings.cors_origin], allow_methods=["*"],
                       allow_headers=["*"])

    @app.middleware("http")
    async def cabecalhos_seguranca(request: Request, call_next):
        resposta = await call_next(request)
        resposta.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:")
        resposta.headers["X-Content-Type-Options"] = "nosniff"
        resposta.headers["Referrer-Policy"] = "same-origin"
        return resposta

    @app.exception_handler(Exception)
    async def erro_generico(request: Request, exc: Exception):
        log.exception("Erro não tratado em %s", request.url.path)  # detalhe só no log (RNF02)
        return JSONResponse(status_code=500, content={"detail": "Algo deu errado. Tente novamente."})

    @app.get("/api/saude", tags=["infra"])
    def saude():
        return {"status": "ok"}

    app.include_router(auth.router)
    app.include_router(tutor.router)
    return app


app = create_app()
