"""Camada de persistência (padrão Repository). Só aqui há consultas ao banco.

Todas as consultas usam o ORM com parâmetros vinculados, sem SQL concatenado.
"""
from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Agendamento, Pet, Profissional, Servico, Usuario


def usuario_por_email(db: Session, email: str) -> Usuario | None:
    return db.scalar(select(Usuario).where(Usuario.email == email.lower()))


def pets_do_tutor(db: Session, id_tutor: int) -> list[Pet]:
    return list(db.scalars(select(Pet).where(Pet.id_tutor == id_tutor, Pet.ativo.is_(True))))


def pet_do_tutor(db: Session, id_pet: int, id_tutor: int) -> Pet | None:
    return db.scalar(select(Pet).where(Pet.id_pet == id_pet, Pet.id_tutor == id_tutor, Pet.ativo.is_(True)))


def servicos_ativos(db: Session) -> list[Servico]:
    return list(db.scalars(select(Servico).where(Servico.ativo.is_(True)).order_by(Servico.id_servico)))


def profissionais_habilitados(db: Session, id_servico: int) -> list[Profissional]:
    stmt = (select(Profissional).where(Profissional.ativo.is_(True))
            .where(Profissional.servicos.any(Servico.id_servico == id_servico)))
    return list(db.scalars(stmt))


def agendamentos_do_dia(db: Session, dia: date, id_profissional: int | None = None) -> list[Agendamento]:
    inicio = datetime.combine(dia, time.min)
    fim = inicio + timedelta(days=1)
    stmt = (select(Agendamento)
            .where(Agendamento.data_hora_inicio >= inicio, Agendamento.data_hora_inicio < fim)
            .where(Agendamento.status != "cancelado")
            .order_by(Agendamento.data_hora_inicio))
    if id_profissional is not None:
        stmt = stmt.where(Agendamento.id_profissional == id_profissional)
    return list(db.scalars(stmt))


def agendamentos_do_tutor(db: Session, id_tutor: int) -> list[Agendamento]:
    stmt = (select(Agendamento).join(Pet).where(Pet.id_tutor == id_tutor)
            .order_by(Agendamento.data_hora_inicio.desc()))
    return list(db.scalars(stmt))


def agendamentos_periodo(db: Session, inicio: date, fim: date) -> list[Agendamento]:
    stmt = (select(Agendamento)
            .where(Agendamento.data_hora_inicio >= datetime.combine(inicio, time.min))
            .where(Agendamento.data_hora_inicio < datetime.combine(fim + timedelta(days=1), time.min)))
    return list(db.scalars(stmt))


def ultimos_concluidos_por_pet(db: Session) -> dict[int, datetime]:
    resultado: dict[int, datetime] = {}
    for ag in db.scalars(select(Agendamento).where(Agendamento.status == "concluido")):
        if ag.id_pet not in resultado or ag.data_hora_inicio > resultado[ag.id_pet]:
            resultado[ag.id_pet] = ag.data_hora_inicio
    return resultado
