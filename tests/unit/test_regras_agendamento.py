"""Testes unitários das regras puras do AgendamentoService (sem banco, sem API)."""
from datetime import date, datetime, time, timedelta

import pytest

from app.models import Agendamento, Profissional, Servico
from app.services.agendamento_service import RegraNegocioErro, calcular_horarios_livres, sobrepoe, validar_transicao

TERCA = date(2030, 1, 1)  # terça-feira
AGORA = datetime(2029, 12, 30, 10, 0)
SERVICO = Servico(id_servico=1, nome="Banho", duracao_pequeno_min=60, duracao_medio_min=90, duracao_grande_min=120)
PROF = Profissional(id_profissional=1, nome="A", hora_inicio=time(9), hora_fim=time(12), dias_trabalho="1,2,3,4,5")


def ag(h_ini, m_ini, h_fim, m_fim, status="agendado", prof=1):
    return Agendamento(id_profissional=prof, status=status,
                       data_hora_inicio=datetime.combine(TERCA, time(h_ini, m_ini)),
                       data_hora_fim=datetime.combine(TERCA, time(h_fim, m_fim)))


@pytest.mark.parametrize("a,b,esperado", [
    ((9, 10), (10, 11), False),   # encostados não se sobrepõem
    ((9, 11), (10, 12), True),
    ((10, 11), (9, 12), True),    # contido
    ((9, 10), (11, 12), False),
])
def test_sobrepoe(a, b, esperado):
    def d(h):
        return datetime.combine(TERCA, time(h))

    assert sobrepoe(d(a[0]), d(a[1]), d(b[0]), d(b[1])) is esperado


def test_horarios_livres_sem_ocupacao_respeita_duracao_e_expediente():
    slots = calcular_horarios_livres(SERVICO, "pequeno", [PROF], [], TERCA, AGORA)
    assert [s.inicio.strftime("%H:%M") for s in slots] == ["09:00", "09:30", "10:00", "10:30", "11:00"]
    assert all(s.fim - s.inicio == timedelta(minutes=60) for s in slots)


def test_horarios_livres_porte_grande_dura_mais():
    slots = calcular_horarios_livres(SERVICO, "grande", [PROF], [], TERCA, AGORA)
    assert slots[-1].inicio.time() == time(10, 0)  # 10:00 + 120 min termina às 12:00


def test_horarios_ocupados_nao_aparecem():
    slots = calcular_horarios_livres(SERVICO, "pequeno", [PROF], [ag(10, 0, 11, 0)], TERCA, AGORA)
    assert [s.inicio.strftime("%H:%M") for s in slots] == ["09:00", "11:00"]


def test_agendamento_cancelado_libera_horario():
    slots = calcular_horarios_livres(SERVICO, "pequeno", [PROF], [ag(10, 0, 11, 0, "cancelado")], TERCA, AGORA)
    assert "10:00" in [s.inicio.strftime("%H:%M") for s in slots]


def test_antecedencia_minima_de_duas_horas():
    agora = datetime.combine(TERCA, time(8, 30))
    slots = calcular_horarios_livres(SERVICO, "pequeno", [PROF], [], TERCA, agora)
    assert slots[0].inicio.time() == time(10, 30)


def test_dia_sem_expediente_nao_tem_horarios():
    domingo = date(2030, 1, 6)
    assert calcular_horarios_livres(SERVICO, "pequeno", [PROF], [], domingo, AGORA) == []


@pytest.mark.parametrize("atual,novo", [("agendado", "confirmado"), ("confirmado", "em_atendimento"),
                                        ("em_atendimento", "concluido"), ("agendado", "cancelado")])
def test_transicoes_validas(atual, novo):
    validar_transicao(atual, novo, datetime(2030, 1, 1, 9), datetime(2030, 1, 1, 10))


@pytest.mark.parametrize("atual,novo", [("concluido", "agendado"), ("cancelado", "confirmado"),
                                        ("agendado", "concluido")])
def test_transicoes_invalidas(atual, novo):
    with pytest.raises(RegraNegocioErro):
        validar_transicao(atual, novo, datetime(2030, 1, 1, 9), datetime(2030, 1, 1, 10))


def test_falta_so_depois_do_horario():
    inicio = datetime(2030, 1, 1, 10)
    with pytest.raises(RegraNegocioErro):
        validar_transicao("agendado", "faltou", inicio, inicio - timedelta(minutes=1))
    validar_transicao("agendado", "faltou", inicio, inicio + timedelta(minutes=15))


def test_alternativas_sao_distintas_e_proximas_do_pedido():
    from app.services.agendamento_service import alternativas
    slots = calcular_horarios_livres(SERVICO, "pequeno", [PROF], [], TERCA, AGORA)
    pedido = datetime.combine(TERCA, time(10))
    alt = alternativas(slots, pedido)
    assert len(alt) == 3 and pedido not in [s.inicio for s in alt]
    assert {s.inicio.time() for s in alt} == {time(9, 30), time(10, 30), time(9, 0)} or \
        {s.inicio.time() for s in alt} == {time(9, 30), time(10, 30), time(11, 0)}
