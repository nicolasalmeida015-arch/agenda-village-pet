"""Testes unitários de segurança: hash Argon2id, bloqueio de login e validação de entrada."""
import pytest
from pydantic import ValidationError

from app import security
from app.schemas import PetCriar, UsuarioCriar


def test_hash_argon2id_nao_guarda_senha_legivel():
    h = security.gerar_hash("minha-senha-forte")
    assert h.startswith("$argon2id$")
    assert "minha-senha-forte" not in h
    assert security.verificar_senha("minha-senha-forte", h)
    assert not security.verificar_senha("errada", h)


def test_hashes_da_mesma_senha_sao_diferentes_por_causa_do_salt():
    assert security.gerar_hash("igual-igual-1") != security.gerar_hash("igual-igual-1")


def test_bloqueio_apos_cinco_falhas():
    security._falhas.clear()
    chave = "x@exemplo.com|1.1.1.1"
    for _ in range(4):
        security.registrar_falha(chave)
    assert not security.login_bloqueado(chave)
    security.registrar_falha(chave)
    assert security.login_bloqueado(chave)


def test_cadastro_exige_consentimento_e_senha_minima():
    with pytest.raises(ValidationError):
        UsuarioCriar(nome="Ana", email="a@exemplo.com", telefone_whatsapp="11 91234-5678", senha="curta",
                     consentimento_lgpd=True)
    with pytest.raises(ValidationError):
        UsuarioCriar(nome="Ana", email="a@exemplo.com", telefone_whatsapp="11 91234-5678",
                     senha="senha-bem-longa", consentimento_lgpd=False)


def test_texto_livre_rejeita_html():
    with pytest.raises(ValidationError):
        PetCriar(nome="Thor", especie="cao", porte="pequeno", pelagem="curta",
                 alergias_observacoes="<script>alert(1)</script>")
