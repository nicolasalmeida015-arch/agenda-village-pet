"""Testes de integração de cadastro, login, logout e proteção de rotas (RF01, RNF01)."""


def test_saude_verifica_o_banco(client):
    r = client.get("/api/saude")
    assert r.status_code == 200
    assert r.json()["status"] == "ok" and r.json()["banco"] == "ok"


def test_saude_retorna_503_quando_o_banco_cai(client, monkeypatch):
    import app.main as principal

    class BancoFora:
        def connect(self):
            raise RuntimeError("sem conexão")

    monkeypatch.setattr(principal, "engine", BancoFora())
    r = client.get("/api/saude")
    assert r.status_code == 503 and r.json()["banco"] == "indisponivel"


def test_cadastro_login_e_eu(client, dados):
    r = client.post("/api/auth/cadastro", json={"nome": "Dani", "email": "Dani@Exemplo.com",
                                                "telefone_whatsapp": "11 91234-5678", "senha": "senha-forte-da-dani",
                                                "consentimento_lgpd": True})
    assert r.status_code == 201 and r.json()["perfil"] == "tutor"
    r = client.post("/api/auth/login", json={"email": "dani@exemplo.com", "senha": "senha-forte-da-dani"})
    token = r.json()["access_token"]
    assert client.get("/api/auth/eu", headers={"Authorization": f"Bearer {token}"}).json()["nome"] == "Dani"


def test_cadastro_email_duplicado_retorna_409(client, dados):
    r = client.post("/api/auth/cadastro", json={"nome": "Outra", "email": "carla@exemplo.com",
                                                "telefone_whatsapp": "11 91234-5678", "senha": "senha-forte-123",
                                                "consentimento_lgpd": True})
    assert r.status_code == 409


def test_login_invalido_tem_mensagem_generica_e_bloqueia(client, dados):
    for _ in range(5):
        r = client.post("/api/auth/login", json={"email": "carla@exemplo.com", "senha": "errada"})
        assert r.status_code == 401 and r.json()["detail"] == "E-mail ou senha inválidos."
    r = client.post("/api/auth/login", json={"email": "carla@exemplo.com", "senha": "senha-de-teste-123"})
    assert r.status_code == 429


def test_logout_invalida_token(client, h_tutor):
    assert client.post("/api/auth/logout", headers=h_tutor).status_code == 204
    assert client.get("/api/auth/eu", headers=h_tutor).status_code == 401


def test_rotas_protegidas_exigem_login(client, dados):
    assert client.get("/api/auth/eu").status_code == 401
    assert client.get("/api/auth/eu", headers={"Authorization": "Bearer token-invalido"}).status_code == 401
