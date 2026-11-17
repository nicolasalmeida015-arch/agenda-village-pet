"""Testes de integração das rotas do tutor (API + serviço + banco)."""
from tests.conftest import as_dt, login


def test_rotas_do_tutor_exigem_login(client, dados):
    assert client.get("/api/pets").status_code == 401
    assert client.get("/api/agendamentos").status_code == 401


def test_cadastrar_e_listar_pets(client, h_tutor):
    r = client.post("/api/pets", headers=h_tutor, json={"nome": "Mel", "especie": "gato", "porte": "pequeno",
                                                        "pelagem": "curta"})
    assert r.status_code == 201
    nomes = [p["nome"] for p in client.get("/api/pets", headers=h_tutor).json()]
    assert nomes == ["Thor", "Mel"]


def test_xss_no_campo_de_observacoes_e_rejeitado(client, h_tutor):
    r = client.post("/api/pets", headers=h_tutor, json={"nome": "Mel", "especie": "gato", "porte": "pequeno",
                                                        "pelagem": "curta",
                                                        "alergias_observacoes": "<script>alert(1)</script>"})
    assert r.status_code == 422


def test_injecao_sql_em_parametro_e_rejeitada(client, h_tutor):
    r = client.get("/api/disponibilidade?id_pet=1 OR 1=1&id_servico=1&dia=2030-01-01", headers=h_tutor)
    assert r.status_code == 422


def test_tutor_nao_ve_pet_de_outro_tutor(client, dados, h_tutor, dia_util):
    rex = dados["rex"]
    r = client.get(f"/api/disponibilidade?id_pet={rex.id_pet}&id_servico=1&dia={dia_util}", headers=h_tutor)
    assert r.status_code == 404


def test_disponibilidade_e_agendamento(client, dados, h_tutor, dia_util):
    thor = dados["thor"]
    slots = client.get(f"/api/disponibilidade?id_pet={thor.id_pet}&id_servico=1&dia={dia_util}",
                       headers=h_tutor).json()
    assert slots[0]["inicio"].endswith("09:00:00")
    r = client.post("/api/agendamentos", headers=h_tutor, json={
        "id_pet": thor.id_pet, "id_servico": 1, "id_profissional": slots[0]["id_profissional"],
        "data_hora_inicio": slots[0]["inicio"]})
    assert r.status_code == 201 and r.json()["status"] == "agendado" and r.json()["origem"] == "online"
    novos = client.get(f"/api/disponibilidade?id_pet={thor.id_pet}&id_servico=1&dia={dia_util}",
                       headers=h_tutor).json()
    assert all(not s["inicio"].endswith("09:00:00") for s in novos)


def test_conflito_retorna_409_com_tres_alternativas(client, dados, h_tutor, dia_util):
    corpo = {"id_pet": dados["thor"].id_pet, "id_servico": 1, "id_profissional": dados["prof"].id_profissional,
             "data_hora_inicio": as_dt(dia_util, 10).isoformat()}
    assert client.post("/api/agendamentos", headers=h_tutor, json=corpo).status_code == 201
    r = client.post("/api/agendamentos", headers=h_tutor, json=corpo)
    assert r.status_code == 409
    assert "acabou de ser reservado" in r.json()["detail"]["mensagem"]
    assert len(r.json()["detail"]["alternativas"]) == 3


def test_tutor_cancela_proprio_agendamento(client, dados, h_tutor, dia_util):
    corpo = {"id_pet": dados["thor"].id_pet, "id_servico": 1, "id_profissional": dados["prof"].id_profissional,
             "data_hora_inicio": as_dt(dia_util, 11).isoformat()}
    ag = client.post("/api/agendamentos", headers=h_tutor, json=corpo).json()
    r = client.post(f"/api/agendamentos/{ag['id_agendamento']}/cancelar", headers=h_tutor)
    assert r.status_code == 200 and r.json()["status"] == "cancelado"


def test_mesmo_horario_vai_para_outro_profissional_livre(client, db, dados, h_tutor, dia_util):
    from app.models import Profissional
    b = Profissional(nome="Profissional B", hora_inicio=dados["prof"].hora_inicio, hora_fim=dados["prof"].hora_fim,
                     dias_trabalho="1,2,3,4,5", servicos=[dados["banho"]])
    db.add(b)
    db.commit()
    corpo = {"id_pet": dados["thor"].id_pet, "id_servico": 1, "id_profissional": dados["prof"].id_profissional,
             "data_hora_inicio": as_dt(dia_util, 15).isoformat()}
    primeiro = client.post("/api/agendamentos", headers=h_tutor, json=corpo).json()
    segundo = client.post("/api/agendamentos", headers=h_tutor, json=corpo)
    assert segundo.status_code == 201
    assert segundo.json()["id_profissional"] != primeiro["id_profissional"]


def test_cancelar_libera_o_horario_e_nao_cancela_duas_vezes(client, dados, h_tutor, dia_util):
    inicio = as_dt(dia_util, 10).isoformat()
    corpo = {"id_pet": dados["thor"].id_pet, "id_servico": 1, "id_profissional": dados["prof"].id_profissional,
             "data_hora_inicio": inicio}
    url_livres = f"/api/disponibilidade?id_pet={dados['thor'].id_pet}&id_servico=1&dia={dia_util}"
    ag = client.post("/api/agendamentos", headers=h_tutor, json=corpo).json()
    assert inicio not in [s["inicio"] for s in client.get(url_livres, headers=h_tutor).json()]

    assert client.post(f"/api/agendamentos/{ag['id_agendamento']}/cancelar", headers=h_tutor).status_code == 200
    assert inicio in [s["inicio"] for s in client.get(url_livres, headers=h_tutor).json()]
    assert client.post(f"/api/agendamentos/{ag['id_agendamento']}/cancelar", headers=h_tutor).status_code == 422


def test_tutor_nao_cancela_agendamento_de_outro_tutor(client, dados, h_tutor, dia_util):
    h_beto = login(client, "beto@exemplo.com")
    corpo = {"id_pet": dados["rex"].id_pet, "id_servico": 1, "id_profissional": dados["prof"].id_profissional,
             "data_hora_inicio": as_dt(dia_util, 13).isoformat()}
    ag = client.post("/api/agendamentos", headers=h_beto, json=corpo).json()
    assert client.post(f"/api/agendamentos/{ag['id_agendamento']}/cancelar", headers=h_tutor).status_code == 404
