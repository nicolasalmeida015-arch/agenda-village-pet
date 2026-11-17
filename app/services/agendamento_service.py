"""Regras de negócio do agendamento (RF02, RF03, RF04, RF05).

As funções puras (sem banco) são testadas em tests/unit; as que usam o banco,
em tests/integration.
"""
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import repositories as repo
from app.config import settings
from app.models import Agendamento, Pet, Profissional, Servico

PASSO_MINUTOS = 30

TRANSICOES = {
    "agendado": {"confirmado", "em_atendimento", "faltou", "cancelado"},
    "confirmado": {"em_atendimento", "faltou", "cancelado"},
    "em_atendimento": {"concluido"},
    "concluido": set(),
    "faltou": set(),
    "cancelado": set(),
}


class RegraNegocioErro(Exception):
    """Violação de regra de negócio com mensagem pronta para o usuário."""


class ConflitoHorario(RegraNegocioErro):
    def __init__(self, alternativas: list["SlotLivre"]):
        super().__init__("Esse horário acabou de ser reservado. Escolha um dos horários livres sugeridos.")
        self.alternativas = alternativas


@dataclass(frozen=True)
class SlotLivre:
    inicio: datetime
    fim: datetime
    id_profissional: int
    profissional: str


def sobrepoe(inicio_a: datetime, fim_a: datetime, inicio_b: datetime, fim_b: datetime) -> bool:
    """Dois intervalos se sobrepõem se um começa antes de o outro terminar."""
    return inicio_a < fim_b and inicio_b < fim_a


def calcular_horarios_livres(servico: Servico, porte: str, profissionais: list[Profissional],
                             ocupados: list[Agendamento], dia: date, agora: datetime) -> list[SlotLivre]:
    """Gera horários em passos de 30 min dentro do expediente, sem sobreposição e com antecedência mínima."""
    duracao = timedelta(minutes=servico.duracao_para(porte))
    limite = agora + timedelta(hours=settings.antecedencia_minima_horas)
    livres: list[SlotLivre] = []
    for prof in profissionais:
        if not prof.trabalha_em(dia.weekday()):
            continue
        cursor = datetime.combine(dia, prof.hora_inicio)
        fim_expediente = datetime.combine(dia, prof.hora_fim)
        ocupados_prof = [a for a in ocupados if a.id_profissional == prof.id_profissional
                         and a.status != "cancelado"]
        while cursor + duracao <= fim_expediente:
            fim = cursor + duracao
            if cursor >= limite and not any(sobrepoe(cursor, fim, a.data_hora_inicio, a.data_hora_fim)
                                             for a in ocupados_prof):
                livres.append(SlotLivre(cursor, fim, prof.id_profissional, prof.nome))
            cursor += timedelta(minutes=PASSO_MINUTOS)
    return sorted(livres, key=lambda s: (s.inicio, s.id_profissional))


def alternativas(livres: list[SlotLivre], pedido: datetime, quantidade: int = 3) -> list[SlotLivre]:
    """Até 3 horários distintos, diferentes do pedido, priorizando os mais próximos dele."""
    unicos: dict[datetime, SlotLivre] = {}
    for s in livres:
        if s.inicio != pedido and s.inicio not in unicos:
            unicos[s.inicio] = s
    return sorted(unicos.values(), key=lambda s: abs((s.inicio - pedido).total_seconds()))[:quantidade]


def validar_transicao(atual: str, novo: str, inicio: datetime, agora: datetime) -> None:
    if novo not in TRANSICOES.get(atual, set()):
        raise RegraNegocioErro(f"Não é possível mudar o status de '{atual}' para '{novo}'.")
    if novo == "faltou" and agora < inicio:
        raise RegraNegocioErro("Só é possível marcar falta depois do horário do atendimento.")


def horarios_livres(db: Session, id_servico: int, pet: Pet, dia: date, agora: datetime) -> list[SlotLivre]:
    servico = db.get(Servico, id_servico)
    if servico is None or not servico.ativo:
        raise RegraNegocioErro("Serviço não encontrado.")
    profissionais = repo.profissionais_habilitados(db, id_servico)
    ocupados = repo.agendamentos_do_dia(db, dia)
    return calcular_horarios_livres(servico, pet.porte, profissionais, ocupados, dia, agora)


def criar_agendamento(db: Session, pet: Pet, id_servico: int, id_profissional: int, inicio: datetime,
                      origem: str, criado_por: int, agora: datetime) -> Agendamento:
    livres = horarios_livres(db, id_servico, pet, inicio.date(), agora)
    mesmo_horario = [s for s in livres if s.inicio == inicio]
    # Preferência pelo profissional pedido; se ele foi ocupado, outro profissional livre no mesmo horário atende.
    escolhido = next((s for s in mesmo_horario if s.id_profissional == id_profissional),
                     mesmo_horario[0] if mesmo_horario else None)
    if escolhido is None:
        raise ConflitoHorario(alternativas(livres, inicio))
    ag = Agendamento(id_pet=pet.id_pet, id_servico=id_servico, id_profissional=escolhido.id_profissional,
                     data_hora_inicio=escolhido.inicio, data_hora_fim=escolhido.fim,
                     status="agendado", origem=origem, criado_por=criado_por)
    db.add(ag)
    try:
        db.commit()
    except IntegrityError:  # reserva simultânea: a restrição única do banco garante um único vencedor
        db.rollback()
        raise ConflitoHorario(alternativas(horarios_livres(db, id_servico, pet, inicio.date(), agora),
                                           inicio)) from None
    db.refresh(ag)
    return ag


def atualizar_status(db: Session, ag: Agendamento, novo: str, agora: datetime) -> Agendamento:
    validar_transicao(ag.status, novo, ag.data_hora_inicio, agora)
    ag.status = novo
    db.commit()
    db.refresh(ag)
    return ag
