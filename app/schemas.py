"""Esquemas Pydantic: validação obrigatória de toda entrada no servidor (RNF02)."""
import re
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

TAG_HTML = re.compile(r"<[^>]+>")


def _sem_html(valor: str | None) -> str | None:
    if valor is not None and TAG_HTML.search(valor):
        raise ValueError("Texto não pode conter marcação HTML.")
    return valor


class UsuarioCriar(BaseModel):
    nome: str = Field(min_length=2, max_length=100)
    email: EmailStr
    telefone_whatsapp: str = Field(pattern=r"^\(?\d{2}\)?\s?9?\d{4}-?\d{4}$")
    senha: str = Field(min_length=10, max_length=128)
    consentimento_lgpd: bool

    _nome = field_validator("nome")(_sem_html)

    @field_validator("consentimento_lgpd")
    @classmethod
    def exige_consentimento(cls, v: bool) -> bool:
        if not v:
            raise ValueError("É preciso aceitar o termo de privacidade para criar a conta.")
        return v


class UsuarioPublico(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id_usuario: int
    nome: str
    email: EmailStr
    perfil: str


class Login(BaseModel):
    email: EmailStr
    senha: str = Field(min_length=1, max_length=128)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    perfil: str


class PetCriar(BaseModel):
    nome: str = Field(min_length=1, max_length=60)
    especie: str = Field(pattern="^(cao|gato)$")
    raca: str | None = Field(default=None, max_length=60)
    porte: str = Field(pattern="^(pequeno|medio|grande)$")
    pelagem: str = Field(pattern="^(curta|media|longa)$")
    alergias_observacoes: str | None = Field(default=None, max_length=500)
    intervalo_retorno_dias: int = Field(default=15, ge=7, le=60)

    _textos = field_validator("nome", "raca", "alergias_observacoes")(_sem_html)


class PetPublico(PetCriar):
    model_config = ConfigDict(from_attributes=True)
    id_pet: int


class ServicoPublico(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id_servico: int
    nome: str
    duracao_pequeno_min: int
    duracao_medio_min: int
    duracao_grande_min: int


class Horario(BaseModel):
    inicio: datetime
    fim: datetime
    id_profissional: int
    profissional: str


class AgendamentoCriar(BaseModel):
    id_pet: int
    id_servico: int
    id_profissional: int
    data_hora_inicio: datetime


class AgendamentoBalcao(AgendamentoCriar):
    origem: str = Field(default="balcao", pattern="^(balcao|telefone)$")


class AgendamentoPublico(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id_agendamento: int
    id_pet: int
    id_servico: int
    id_profissional: int
    data_hora_inicio: datetime
    data_hora_fim: datetime
    status: str
    origem: str


class ItemAgendaDia(AgendamentoPublico):
    pet_nome: str
    pet_porte: str
    pet_alergias: str | None
    servico_nome: str
    profissional_nome: str


class AtualizarStatus(BaseModel):
    status: str = Field(pattern="^(confirmado|em_atendimento|concluido|faltou|cancelado)$")


class Indicadores(BaseModel):
    inicio: date
    fim: date
    total_agendamentos: int
    faltas: int
    taxa_faltas: float
    ocupacao: float
    servicos_mais_procurados: list[dict]
    pets_sem_retorno: int
