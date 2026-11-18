"""Ponto de entrada da API Agenda Village Pet."""
import logging
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.config import settings
from app.database import Base, engine
from app.routers import auth, equipe, tutor

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("app")
log_req = logging.getLogger("requisicoes")


def create_app() -> FastAPI:
    settings.validar()
    Base.metadata.create_all(bind=engine)
    if settings.seed_demo:  # demonstração pública com dados fictícios
        from app.seed import popular
        popular()
    app = FastAPI(title="Agenda Village Pet", version="1.0.0",
                  description="MVP de agendamento de banho e tosa - Village Pet BR-116")
    app.add_middleware(CORSMiddleware, allow_origins=[settings.cors_origin], allow_methods=["*"],
                       allow_headers=["*"])

    @app.middleware("http")
    async def cabecalhos_seguranca(request: Request, call_next):
        inicio = time.perf_counter()
        resposta = await call_next(request)
        if request.url.path.startswith("/api/"):  # monitoramento: método, rota, status e tempo (sem query string)
            log_req.info("%s %s %s %.0fms", request.method, request.url.path, resposta.status_code,
                         (time.perf_counter() - inicio) * 1000)
        resposta.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:")
        resposta.headers["X-Content-Type-Options"] = "nosniff"
        resposta.headers["Referrer-Policy"] = "same-origin"
        return resposta

    @app.exception_handler(Exception)
    async def erro_generico(request: Request, exc: Exception):
        log.exception("Erro não tratado em %s", request.url.path)  # detalhe só no log (RNF02)
        return JSONResponse(status_code=500, content={"detail": "Algo deu errado. Tente novamente."})

    # HEAD também: monitores de disponibilidade (ex.: UptimeRobot) checam com HEAD; sem isso a requisição caía no
    # servidor de arquivos estáticos e respondia 404, marcando o app como DOWN.
    @app.api_route("/api/saude", methods=["GET", "HEAD"], tags=["infra"])
    def saude():
        """Verificação de saúde usada pelo Render (health check) e pelo UptimeRobot: testa também o banco."""
        try:
            with engine.connect() as conexao:
                conexao.execute(text("SELECT 1"))
        except Exception:
            log.exception("Banco indisponível na verificação de saúde")
            return JSONResponse(status_code=503, content={"status": "erro", "banco": "indisponivel"})
        return {"status": "ok", "banco": "ok", "versao": app.version}

    app.include_router(auth.router)
    app.include_router(tutor.router)
    app.include_router(equipe.router)
    app.mount("/", StaticFiles(directory="app/static", html=True), name="static")
    return app


app = create_app()
