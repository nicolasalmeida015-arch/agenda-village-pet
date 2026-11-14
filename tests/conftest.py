from datetime import date, datetime, time, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import security
from app.database import Base, get_db
from app.main import app
from app.models import Pet, Profissional, Servico, Usuario

SENHA = "senha-de-teste-123"


def proximo_dia_util(base: date | None = None) -> date:
    """Próxima terça a sábado com pelo menos 2 dias de folga (expediente dos profissionais de teste)."""
    d = (base or date.today()) + timedelta(days=2)
    while d.weekday() not in (1, 2, 3, 4, 5):
        d += timedelta(days=1)
    return d


@pytest.fixture()
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Sessao = sessionmaker(bind=engine, expire_on_commit=False)
    sessao = Sessao()
    yield sessao
    sessao.close()


@pytest.fixture()
def dados(db):
    banho = Servico(nome="Banho", duracao_pequeno_min=60, duracao_medio_min=90, duracao_grande_min=120)
    tosa = Servico(nome="Tosa completa", duracao_pequeno_min=120, duracao_medio_min=150, duracao_grande_min=180)
    db.add_all([banho, tosa])
    prof = Profissional(nome="Profissional A", hora_inicio=time(9), hora_fim=time(17),
                        dias_trabalho="1,2,3,4,5", servicos=[banho, tosa])
    db.add(prof)
    h = security.gerar_hash(SENHA)
    tutor = Usuario(nome="Carla", email="carla@exemplo.com", telefone_whatsapp="11 90000-0000", senha_hash=h,
                    perfil="tutor", consentimento_lgpd=True)
    outro = Usuario(nome="Beto", email="beto@exemplo.com", telefone_whatsapp="11 90000-0003", senha_hash=h,
                    perfil="tutor", consentimento_lgpd=True)
    atendente = Usuario(nome="Ana", email="atendente@exemplo.com", telefone_whatsapp="11 90000-0001",
                        senha_hash=h, perfil="atendente", consentimento_lgpd=True)
    gerente = Usuario(nome="Gil", email="gerente@exemplo.com", telefone_whatsapp="11 90000-0002",
                      senha_hash=h, perfil="gerente", consentimento_lgpd=True)
    db.add_all([tutor, outro, atendente, gerente])
    db.flush()
    thor = Pet(id_tutor=tutor.id_usuario, nome="Thor", especie="cao", porte="pequeno", pelagem="longa",
               alergias_observacoes="Pele sensível")
    rex = Pet(id_tutor=outro.id_usuario, nome="Rex", especie="cao", porte="grande", pelagem="curta")
    db.add_all([thor, rex])
    db.commit()
    return {"banho": banho, "tosa": tosa, "prof": prof, "tutor": tutor, "outro": outro,
            "atendente": atendente, "gerente": gerente, "thor": thor, "rex": rex}


@pytest.fixture()
def client(db):
    security._falhas.clear()
    security._revogados.clear()
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def login(client, email: str, senha: str = SENHA) -> dict:
    r = client.post("/api/auth/login", json={"email": email, "senha": senha})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture()
def h_tutor(client, dados):
    return login(client, "carla@exemplo.com")


@pytest.fixture()
def h_atendente(client, dados):
    return login(client, "atendente@exemplo.com")


@pytest.fixture()
def h_gerente(client, dados):
    return login(client, "gerente@exemplo.com")


@pytest.fixture()
def dia_util():
    return proximo_dia_util()


def as_dt(dia: date, hora: int, minuto: int = 0) -> datetime:
    return datetime.combine(dia, time(hora, minuto))
