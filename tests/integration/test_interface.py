"""Interface web: telas servidas pela API e recurso de acessibilidade presente em todas elas."""
import pytest

TELAS = ["/", "/cadastro.html", "/pets.html", "/agendar.html", "/equipe.html"]


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
