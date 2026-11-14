"""Entidades do MVP (modelagem definida na Experiência Prática II)."""
from datetime import datetime, time, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Table,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def agora_utc() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)

PERFIS = ("tutor", "atendente", "gerente")
PORTES = ("pequeno", "medio", "grande")
STATUS = ("agendado", "confirmado", "em_atendimento", "concluido", "faltou", "cancelado")
ORIGENS = ("online", "balcao", "telefone")

profissional_servico = Table(
    "profissional_servico",
    Base.metadata,
    Column("id_profissional", ForeignKey("profissional.id_profissional"), primary_key=True),
    Column("id_servico", ForeignKey("servico.id_servico"), primary_key=True),
)


class Usuario(Base):
    __tablename__ = "usuario"
    id_usuario: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    telefone_whatsapp: Mapped[str] = mapped_column(String(20))
    senha_hash: Mapped[str] = mapped_column(String(255))
    perfil: Mapped[str] = mapped_column(String(20), default="tutor")
    consentimento_lgpd: Mapped[bool] = mapped_column(Boolean, default=False)
    data_consentimento: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=agora_utc)

    pets: Mapped[list["Pet"]] = relationship(back_populates="tutor")


class Pet(Base):
    __tablename__ = "pet"
    __table_args__ = (
        CheckConstraint("intervalo_retorno_dias BETWEEN 7 AND 60", name="ck_intervalo_retorno"),
    )
    id_pet: Mapped[int] = mapped_column(primary_key=True)
    id_tutor: Mapped[int] = mapped_column(ForeignKey("usuario.id_usuario"), index=True)
    nome: Mapped[str] = mapped_column(String(60))
    especie: Mapped[str] = mapped_column(String(10))
    raca: Mapped[str | None] = mapped_column(String(60), nullable=True)
    porte: Mapped[str] = mapped_column(String(10))
    pelagem: Mapped[str] = mapped_column(String(10))
    alergias_observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)
    intervalo_retorno_dias: Mapped[int] = mapped_column(Integer, default=15)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)

    tutor: Mapped[Usuario] = relationship(back_populates="pets")


class Servico(Base):
    __tablename__ = "servico"
    id_servico: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(60), unique=True)
    duracao_pequeno_min: Mapped[int] = mapped_column(Integer)
    duracao_medio_min: Mapped[int] = mapped_column(Integer)
    duracao_grande_min: Mapped[int] = mapped_column(Integer)
    preco_referencia: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)

    def duracao_para(self, porte: str) -> int:
        return {"pequeno": self.duracao_pequeno_min, "medio": self.duracao_medio_min,
                "grande": self.duracao_grande_min}[porte]


class Profissional(Base):
    __tablename__ = "profissional"
    id_profissional: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100))
    hora_inicio: Mapped[time] = mapped_column(Time)
    hora_fim: Mapped[time] = mapped_column(Time)
    dias_trabalho: Mapped[str] = mapped_column(String(40), default="1,2,3,4,5")  # 0=segunda ... 6=domingo
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)

    servicos: Mapped[list[Servico]] = relationship(secondary=profissional_servico)

    def trabalha_em(self, weekday: int) -> bool:
        return str(weekday) in self.dias_trabalho.split(",")


class Agendamento(Base):
    __tablename__ = "agendamento"
    __table_args__ = (
        UniqueConstraint("id_profissional", "data_hora_inicio", name="uq_profissional_horario"),
    )
    id_agendamento: Mapped[int] = mapped_column(primary_key=True)
    id_pet: Mapped[int] = mapped_column(ForeignKey("pet.id_pet"), index=True)
    id_servico: Mapped[int] = mapped_column(ForeignKey("servico.id_servico"))
    id_profissional: Mapped[int] = mapped_column(ForeignKey("profissional.id_profissional"))
    data_hora_inicio: Mapped[datetime] = mapped_column(DateTime, index=True)
    data_hora_fim: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(20), default="agendado")
    origem: Mapped[str] = mapped_column(String(10), default="online")
    criado_por: Mapped[int] = mapped_column(ForeignKey("usuario.id_usuario"))
    lembrete_enviado_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=agora_utc)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime, default=agora_utc,
                                                    onupdate=agora_utc)

    pet: Mapped[Pet] = relationship()
    servico: Mapped[Servico] = relationship()
    profissional: Mapped[Profissional] = relationship()
