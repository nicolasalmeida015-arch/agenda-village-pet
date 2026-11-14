"""Testes de integração das rotas da equipe e controle de acesso por perfil."""
from datetime import timedelta

from app.models import Agendamento
from tests.conftest import as_dt


def _agendar(client, h, dados, dia, hora):
    corpo = {"id_pet": dados["thor"].id_pet, "id_servico": 1, "id_profissional": dados["prof"].id_profissional,
             "data_hora_inicio": as_dt(dia, hora).isoformat()}
    return client.post("/api/agendamentos", headers=h, json=corpo).json()


def test_agenda_da_equipe_exige_login(client, dados, dia_util):
    assert client.get(f"/api/equipe/agenda?dia={dia_util}").status_code == 401


def test_tutor_nao_acessa_agenda_da_equipe(client, h_tutor, dia_util):
    assert client.get(f"/api/equipe/agenda?dia={dia_util}", headers=h_tutor).status_code == 403


def test_atendente_ve_agenda_com_ficha_do_pet(client, dados, h_tutor, h_atendente, dia_util):
    _agendar(client, h_tutor, dados, dia_util, 9)
    itens = client.get(f"/api/equipe/agenda?dia={dia_util}", headers=h_atendente).json()
    assert len(itens) == 1
    assert itens[0]["pet_nome"] == "Thor" and itens[0]["pet_alergias"] == "Pele sensível"


def test_fluxo_de_status(client, dados, h_tutor, h_atendente, dia_util):
    ag = _agendar(client, h_tutor, dados, dia_util, 9)
    url = f"/api/equipe/agendamentos/{ag['id_agendamento']}/status"
    for novo in ("confirmado", "em_atendimento", "concluido"):
        r = client.patch(url, headers=h_atendente, json={"status": novo})
        assert r.status_code == 200 and r.json()["status"] == novo
    assert client.patch(url, headers=h_atendente, json={"status": "confirmado"}).status_code == 422


def test_falta_antes_do_horario_e_recusada(client, dados, h_tutor, h_atendente, dia_util):
    ag = _agendar(client, h_tutor, dados, dia_util, 9)
    r = client.patch(f"/api/equipe/agendamentos/{ag['id_agendamento']}/status", headers=h_atendente,
                     json={"status": "faltou"})
    assert r.status_code == 422


def test_balcao_bloqueia_mesmo_horario_online(client, dados, h_tutor, h_atendente, dia_util):
    corpo = {"id_pet": dados["rex"].id_pet, "id_servico": 1, "id_profissional": dados["prof"].id_profissional,
             "data_hora_inicio": as_dt(dia_util, 14).isoformat(), "origem": "telefone"}
    r = client.post("/api/equipe/agendamentos", headers=h_atendente, json=corpo)
    assert r.status_code == 201 and r.json()["origem"] == "telefone"
    slots = client.get(f"/api/disponibilidade?id_pet={dados['thor'].id_pet}&id_servico=1&dia={dia_util}",
                       headers=h_tutor).json()
    horas = [s["inicio"][11:16] for s in slots]
    assert "14:00" not in horas and "13:30" not in horas  # 13:30 + 60 min invadiria 14:00


def test_indicadores_so_para_gerente(client, dados, db, h_atendente, h_gerente, dia_util):
    assert client.get(f"/api/equipe/indicadores?inicio={dia_util}&fim={dia_util}",
                      headers=h_atendente).status_code == 403
    for hora, status in ((9, "concluido"), (10, "concluido"), (11, "concluido"), (12, "faltou")):
        db.add(Agendamento(id_pet=dados["thor"].id_pet, id_servico=1, id_profissional=1,
                           data_hora_inicio=as_dt(dia_util, hora),
                           data_hora_fim=as_dt(dia_util, hora) + timedelta(hours=1),
                           status=status, origem="balcao", criado_por=dados["atendente"].id_usuario))
    db.commit()
    r = client.get(f"/api/equipe/indicadores?inicio={dia_util}&fim={dia_util}", headers=h_gerente)
    assert r.status_code == 200
    assert r.json()["taxa_faltas"] == 25.0 and r.json()["total_agendamentos"] == 4


def test_lembretes_da_vespera(client, dados, db, h_gerente):
    from datetime import date, datetime, time
    amanha = date.today() + timedelta(days=1)
    db.add(Agendamento(id_pet=dados["thor"].id_pet, id_servico=1, id_profissional=1,
                       data_hora_inicio=datetime.combine(amanha, time(9)),
                       data_hora_fim=datetime.combine(amanha, time(10)), status="agendado", origem="online",
                       criado_por=dados["tutor"].id_usuario))
    db.commit()
    primeiro = client.post("/api/equipe/lembretes/vespera", headers=h_gerente).json()
    assert len(primeiro) == 1 and primeiro[0]["link_whatsapp"].startswith("https://wa.me/55")
    assert client.post("/api/equipe/lembretes/vespera", headers=h_gerente).json() == []  # envia uma vez só


def test_cabecalhos_de_seguranca(client):
    r = client.get("/api/saude")
    assert "default-src 'self'" in r.headers["content-security-policy"]
    assert r.headers["x-content-type-options"] == "nosniff"
