"""Configuração de implantação: URL do banco do provedor e segredo obrigatório em produção."""
import pytest

from app.config import SEGREDO_DEV, Settings, normalizar_database_url


@pytest.mark.parametrize("entrada", ["postgres://u:s@host/db", "postgresql://u:s@host/db"])
def test_url_do_provedor_passa_a_usar_o_driver_psycopg(entrada):
    assert normalizar_database_url(entrada) == "postgresql+psycopg://u:s@host/db"


def test_url_sqlite_e_psycopg_ficam_iguais():
    assert normalizar_database_url("sqlite:///./agenda.db") == "sqlite:///./agenda.db"
    assert normalizar_database_url("postgresql+psycopg://u@h/d") == "postgresql+psycopg://u@h/d"


def test_producao_recusa_segredo_padrao():
    with pytest.raises(RuntimeError):
        Settings(ambiente="producao", jwt_secret=SEGREDO_DEV).validar()


def test_producao_aceita_segredo_forte():
    Settings(ambiente="producao", jwt_secret="x" * 40).validar()
