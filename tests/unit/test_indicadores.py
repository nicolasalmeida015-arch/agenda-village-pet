"""Testes unitários do cálculo de indicadores, retorno e lembretes."""
from datetime import date, datetime, time

from app.models import Agendamento, Pet, Profissional, Servico
from app.services.indicador_service import calcular_indicadores, pets_para_retorno
from app.services.lembrete_service import link_whatsapp


def _ag(status, h, servico):
    return Agendamento(status=status, servico=servico, data_hora_inicio=datetime(2030, 1, 1, h),
                       data_hora_fim=datetime(2030, 1, 1, h + 1))


def test_indicadores_taxa_de_faltas_e_ocupacao():
    banho = Servico(nome="Banho", duracao_pequeno_min=60, duracao_medio_min=60, duracao_grande_min=60)
    prof = Profissional(nome="A", hora_inicio=time(9), hora_fim=time(17), dias_trabalho="1", ativo=True)
    ags = [_ag("concluido", 9, banho), _ag("concluido", 10, banho), _ag("concluido", 11, banho),
           _ag("faltou", 12, banho), _ag("cancelado", 13, banho)]
    r = calcular_indicadores(ags, [prof], date(2030, 1, 1), date(2030, 1, 1))
    assert r["total_agendamentos"] == 4           # cancelado não conta
    assert r["faltas"] == 1 and r["taxa_faltas"] == 25.0
    assert r["ocupacao"] == 37.5                  # 3 h atendidas / 8 h de expediente
    assert r["servicos_mais_procurados"][0] == {"servico": "Banho", "quantidade": 4}


def test_pets_para_retorno():
    thor = Pet(id_pet=1, nome="Thor", intervalo_retorno_dias=15)
    rex = Pet(id_pet=2, nome="Rex", intervalo_retorno_dias=15)
    bob = Pet(id_pet=3, nome="Bob", intervalo_retorno_dias=15)
    ultimos = {1: datetime(2030, 1, 1, 10), 2: datetime(2030, 1, 10, 10), 3: datetime(2030, 1, 1, 10)}
    devidos = pets_para_retorno([thor, rex, bob], ultimos, com_futuro={3}, hoje=date(2030, 1, 16))
    assert [p.nome for p in devidos] == ["Thor"]


def test_link_whatsapp_pre_preenchido():
    assert link_whatsapp("11 91234-5678", "Olá Thor").startswith("https://wa.me/5511912345678?text=Ol%C3%A1")
