"""Painel da gerência (RF08): faltas, ocupação, serviços mais procurados e pets sem retorno."""
from collections import Counter
from datetime import date, datetime, timedelta

from app.models import Agendamento, Pet, Profissional


def calcular_indicadores(agendamentos: list[Agendamento], profissionais: list[Profissional],
                         inicio: date, fim: date) -> dict:
    validos = [a for a in agendamentos if a.status != "cancelado"]
    finalizados = [a for a in validos if a.status in ("concluido", "faltou")]
    faltas = sum(1 for a in finalizados if a.status == "faltou")
    taxa_faltas = round(faltas / len(finalizados) * 100, 1) if finalizados else 0.0

    minutos_disponiveis = 0
    dia = inicio
    while dia <= fim:
        for p in profissionais:
            if p.ativo and p.trabalha_em(dia.weekday()):
                ini = datetime.combine(dia, p.hora_inicio)
                fim_exp = datetime.combine(dia, p.hora_fim)
                minutos_disponiveis += int((fim_exp - ini).total_seconds() // 60)
        dia += timedelta(days=1)
    minutos_ocupados = sum(int((a.data_hora_fim - a.data_hora_inicio).total_seconds() // 60)
                           for a in validos if a.status != "faltou")
    ocupacao = round(minutos_ocupados / minutos_disponiveis * 100, 1) if minutos_disponiveis else 0.0

    contagem = Counter(a.servico.nome for a in validos)
    mais_procurados = [{"servico": nome, "quantidade": qtd} for nome, qtd in contagem.most_common(3)]
    return {"total_agendamentos": len(validos), "faltas": faltas, "taxa_faltas": taxa_faltas,
            "ocupacao": ocupacao, "servicos_mais_procurados": mais_procurados}


def pets_para_retorno(pets: list[Pet], ultimos: dict[int, datetime], com_futuro: set[int],
                      hoje: date) -> list[Pet]:
    """RF07: pets cujo último banho concluído passou do intervalo e sem agendamento futuro."""
    devidos = []
    for pet in pets:
        ultimo = ultimos.get(pet.id_pet)
        if ultimo is None or pet.id_pet in com_futuro:
            continue
        if (hoje - ultimo.date()).days >= pet.intervalo_retorno_dias:
            devidos.append(pet)
    return devidos
