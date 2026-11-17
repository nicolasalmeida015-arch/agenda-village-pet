"""Interface web: telas servidas pela API e recurso de acessibilidade presente em todas elas."""
import pytest

TELAS = ["/", "/cadastro.html", "/pets.html", "/agendar.html", "/equipe.html", "/painel.html"]


@pytest.mark.parametrize("tela", TELAS)
def test_toda_tela_carrega_o_recurso_de_acessibilidade_no_head(client, tela):
    r = client.get(tela)
    assert r.status_code == 200
    head = r.text.split("</head>")[0]
    assert '<script src="/js/acessibilidade.js"></script>' in head


def test_script_de_acessibilidade_e_servido_e_respeita_a_csp(client):
    r = client.get("/js/acessibilidade.js")
    assert r.status_code == 200
    assert "javascript" in r.headers["content-type"]
    assert "aria-pressed" in r.text
    assert "innerHTML" not in r.text  # textContent apenas, coerente com a política de XSS
    csp = client.get("/").headers["content-security-policy"]
    assert "script-src 'self'" in csp


def test_aviso_de_conflito_fica_junto_da_grade_de_horarios(client):
    html = client.get("/agendar.html").text
    escolha = html.split('id="passo-escolha"')[1].split("</section>\n\n")[0]
    assert escolha.index('id="conflito"') < escolha.index('id="horas"')
    assert 'id="dica-conflito"' in escolha


def test_agenda_da_equipe_tem_resumo_e_destaque_de_cuidado_especial(client):
    assert 'id="resumo-dia"' in client.get("/equipe.html").text
    js = client.get("/js/equipe.js").text
    assert "Cuidado especial" in js and "linha-cuidado" in js
    assert ".cuidado{" in client.get("/css/app.css").text


def test_painel_da_gerencia_usa_indicadores_e_lembretes(client):
    js = client.get("/js/painel.js").text
    assert "/api/equipe/indicadores" in js and "/api/equipe/lembretes/vespera" in js
    assert 'eu.perfil !== "gerente"' in js
    assert "innerHTML" not in js
